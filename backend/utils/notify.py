"""Google Chat / generic webhook (optional channel for reminders)."""
import json
import urllib.request


def post_webhook(url, text):
    if not url:
        return False
    try:
        req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as err:
        print("webhook failed:", err)
        return False
