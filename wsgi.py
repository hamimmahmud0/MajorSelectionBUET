"""
WSGI entry point for production servers (Gunicorn / Uvicorn).

Usage:
    gunicorn wsgi:app -w 4 -b 0.0.0.0:8000
    uvicorn wsgi:app --host 0.0.0.0 --port 8000 --workers 4

For development:
    python wsgi.py
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
