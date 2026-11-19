import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me-please-32-bytes")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "emp.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    CELERY_BROKER_URL = REDIS_URL + "/0"
    CELERY_RESULT_BACKEND = REDIS_URL + "/1"
    TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")

    CACHE_URL = REDIS_URL + "/2"
    CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() != "false"
    CACHE_TTL_SHORT = int(os.environ.get("CACHE_TTL_SHORT", 60))    
    CACHE_TTL_LONG = int(os.environ.get("CACHE_TTL_LONG", 600))     

    REMINDER_HOUR = int(os.environ.get("REMINDER_HOUR", 8))        
    REMINDER_MINUTE = int(os.environ.get("REMINDER_MINUTE", 0))
    REPORT_DAY = int(os.environ.get("REPORT_DAY", 1))              
    REPORT_HOUR = int(os.environ.get("REPORT_HOUR", 7))

    GCHAT_WEBHOOK_URL = os.environ.get("GCHAT_WEBHOOK_URL")

    EXPORT_DIR = os.path.join(BASE_DIR, "exports")
    REPORT_DIR = os.path.join(BASE_DIR, "reports")

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@emp.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    ADMIN_NAME = "System Admin"