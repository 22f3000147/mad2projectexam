"""Redis cache for the API (db 2).

How it works
  1. remember(key, ttl, build): return the cached value, or run build(), store it and return it.
  2. Every key lives in a "group" (the text before the first colon, e.g. exams:open -> group exams).
  3. DEPENDS says which tables a group is built from. When a commit changes one of those tables
     the whole group is cleared automatically - so routes never have to remember to clear it.
  4. Every key also has a TTL, so even a missed refresh fixes itself in at most a few minutes.
  5. If Redis is down the app still works: remember() just calls build() every time.
"""
import hashlib
import json
import time
import redis
from flask import g, has_request_context
from sqlalchemy import event
from sqlalchemy.orm import Session
from config import Config
from models import User, Course, Examination, ExaminationRubric, ExaminationSlot, Booking

ENABLED = Config.CACHE_ENABLED
PREFIX = "emp:" + hashlib.md5(Config.SQLALCHEMY_DATABASE_URI.encode()).hexdigest()[:6] + ":"
MISS = object()

DEPENDS = {
    "stats": (User, Course, Examination, ExaminationSlot, Booking),       
    "rubrics": (ExaminationRubric,),                                      
    "exams": (Course, Examination, ExaminationSlot, Booking),             
    "slots": (Course, Examination, ExaminationSlot, Booking, User),       
}

_client = None
_down_until = 0.0


def _redis():
    global _client
    if not ENABLED or time.time() < _down_until:
        return None
    if _client is None:
        _client = redis.Redis.from_url(Config.CACHE_URL, socket_connect_timeout=0.3,
                                       socket_timeout=0.3, decode_responses=True)
    return _client


def _redis_failed():
    """Redis problem: skip the cache for 5 seconds instead of waiting on timeouts every request."""
    global _down_until
    _down_until = time.time() + 5


def _mark(status):
    if has_request_context() and g.get("cache") != "MISS":
        g.cache = status                     


def remember(key, ttl, build):
    r = _redis()
    if r is not None:
        try:
            raw = r.get(PREFIX + key)
            if raw is not None:
                r.hincrby(PREFIX + "meta", "hits", 1)
                _mark("HIT")
                return json.loads(raw)
            r.hincrby(PREFIX + "meta", "misses", 1)
        except redis.RedisError:
            _redis_failed()
            r = None
    value = build()
    _mark("MISS")
    if r is not None:
        try:
            r.setex(PREFIX + key, ttl, json.dumps(value))
        except redis.RedisError:
            _redis_failed()
    return value


def clear_group(group):
    r = _redis()
    if r is None:
        return
    try:
        keys = list(r.scan_iter(match=f"{PREFIX}{group}:*", count=200))
        if keys:
            r.delete(*keys)
    except redis.RedisError:
        _redis_failed()


def clear_all():
    for group in DEPENDS:
        clear_group(group)


def cache_info():
    r = _redis()
    if r is None:
        return {"enabled": False, "hits": 0, "misses": 0, "keys": []}
    try:
        meta = r.hgetall(PREFIX + "meta")
        keys = [{"key": k[len(PREFIX):], "ttl": r.ttl(k)}
                for k in sorted(r.scan_iter(match=PREFIX + "*")) if k != PREFIX + "meta"]
        return {"enabled": True, "hits": int(meta.get("hits", 0)), "misses": int(meta.get("misses", 0)), "keys": keys}
    except redis.RedisError:
        _redis_failed()
        return {"enabled": False, "hits": 0, "misses": 0, "keys": []}


@event.listens_for(Session, "before_flush")
def _note_changed_tables(session, flush_context, instances):
    changed = session.info.setdefault("changed_tables", set())
    for obj in (*session.new, *session.dirty, *session.deleted):
        changed.add(type(obj))


@event.listens_for(Session, "after_commit")
def _clear_changed_groups(session):
    changed = session.info.pop("changed_tables", set())
    for group, tables in DEPENDS.items():
        if changed.intersection(tables):
            clear_group(group)


@event.listens_for(Session, "after_rollback")
def _forget_changes(session):
    session.info.pop("changed_tables", None)
