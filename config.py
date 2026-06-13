import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # ─── Student ID Validation ───
    # First 4 digits that every valid student ID must start with
    STUDENT_ID_PREFIX = os.getenv('STUDENT_ID_PREFIX', '2104')

    # ─── Database ───
    # In production, DATABASE_URI should be an absolute path.
    # Default: <project_root>/instance/major_selection.db
    _db_uri = os.getenv('DATABASE_URI', '')
    if _db_uri:
        SQLALCHEMY_DATABASE_URI = _db_uri
    else:
        _instance = Path(__file__).resolve().parent / 'instance'
        _instance.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{_instance / 'major_selection.db'}"

    # ─── Session ───
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ─── Production security ───
    PRODUCTION = os.getenv('PRODUCTION', 'false').lower() in ('true', '1', 'yes')
    if PRODUCTION:
        SESSION_COOKIE_SECURE = True
        DEBUG = False
        # Set to your production domain
        SERVER_NAME = os.getenv('SERVER_NAME', None)
    WTF_CSRF_ENABLED = True
