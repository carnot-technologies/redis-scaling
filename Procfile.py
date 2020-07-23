web: gunicorn redisscale.wsgi
monitor: python scheduler.py