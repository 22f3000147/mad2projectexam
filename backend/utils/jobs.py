"""Start Celery jobs from the API and read their status."""
import redis
from celery.result import AsyncResult
from celery_app import celery
from config import Config
from utils.helpers import ApiError

NOT_RUNNING = "Background service is not running. Start Redis and the Celery worker."


def check_redis():
    """Fail fast (1 second) instead of letting Celery retry the connection for a long time."""
    try:
        redis.Redis.from_url(Config.CELERY_BROKER_URL, socket_connect_timeout=1, socket_timeout=1).ping()
    except Exception:
        raise ApiError(NOT_RUNNING, 503)


def start_job(task, *args, **kwargs):
    check_redis()
    try:
        return task.apply_async(args=args, kwargs=kwargs, retry=False).id
    except Exception:
        raise ApiError(NOT_RUNNING, 503)


def job_status(task_id):
    check_redis()
    try:
        result = AsyncResult(task_id, app=celery)
        state = result.state                      
        return {"state": state,
                "result": result.result if state == "SUCCESS" else None,
                "error": str(result.result) if state == "FAILURE" else None}
    except Exception:
        raise ApiError(NOT_RUNNING, 503)
