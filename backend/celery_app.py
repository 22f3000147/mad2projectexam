"""Celery setup. Start with:
    celery -A celery_app.celery worker --loglevel=info      (add --pool=solo on Windows)
    celery -A celery_app.celery beat --loglevel=info        (the scheduler)
"""
from celery import Celery
from celery.schedules import crontab
from config import Config

celery = Celery("emp", broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND,
                include=["tasks"])

celery.conf.update(
    timezone=Config.TIMEZONE,
    enable_utc=False,
    result_expires=60 * 60 * 24,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "daily-exam-reminders": {
            "task": "tasks.send_daily_reminders",
            "schedule": crontab(hour=Config.REMINDER_HOUR, minute=Config.REMINDER_MINUTE),
        },
        "monthly-exam-report": {
            "task": "tasks.send_monthly_report",
            "schedule": crontab(day_of_month=Config.REPORT_DAY, hour=Config.REPORT_HOUR, minute=0),
        },
    },
)

_flask_app = None


def get_flask_app():
    """Tasks need the Flask app (database etc). Built once per worker, lazily to avoid import loops."""
    global _flask_app
    if _flask_app is None:
        from app import create_app
        _flask_app = create_app()
    return _flask_app


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with get_flask_app().app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask
