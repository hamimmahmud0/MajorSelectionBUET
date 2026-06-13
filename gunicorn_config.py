"""
Gunicorn configuration file for production deployment.

Usage:
    gunicorn wsgi:app -c gunicorn_config.py
"""
import os
from pathlib import Path

# ─── Bind ───
# Use a Unix socket for nginx reverse proxy, or TCP for direct access.
# Override via environment variable: GUNICORN_BIND
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')

# ─── Workers ───
# Recommended: (2 × CPU cores) + 1
# Override via: GUNICORN_WORKERS
workers = int(os.getenv('GUNICORN_WORKERS', '4'))
worker_class = 'sync'
threads = int(os.getenv('GUNICORN_THREADS', '2'))

# ─── Timeouts ───
timeout = 120
graceful_timeout = 30
keepalive = 5

# ─── Logging ───
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')   # stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')      # stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# ─── Process Name ───
proc_name = 'buet-major-selection'

# ─── Daemon (set to true only when using systemd) ───
daemon = False

# ─── PID file ───
pidfile = os.getenv('GUNICORN_PIDFILE', '/tmp/buet-major-selection.pid')

# ─── User/Group (set when running as root) ───
# user = 'www-data'
# group = 'www-data'

# ─── Preload app for faster worker spawn ───
preload_app = True
