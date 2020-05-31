import os

# Email config
ENABLE_EMAILS = int(os.environ.get('ENABLE_EMAILS', 1))
EMAIL_PREFIX = os.environ.get('EMAIL_PREFIX', '[RedisScale]')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_USE_TLS = bool(int(os.environ.get('EMAIL_USE_TLS', 1)))
SERVER_EMAIL = os.environ.get('SERVER_EMAIL')
RECIPIENTS = os.environ.get('RECIPIENTS').split(',') if os.environ.get('RECIPIENTS') else []

# Heroku API
HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY')

# Logging
N_RETENTION_DAYS = int(os.environ.get('N_RETENTION_DAYS', 5))
