"""
WSGI entry point for production servers (Gunicorn / Uvicorn).

Usage:
    gunicorn wsgi:app -w 4 -b 0.0.0.0:8000
    uvicorn wsgi:app --host 0.0.0.0 --port 8000 --workers 4
"""
from app import create_app

app = create_app()
