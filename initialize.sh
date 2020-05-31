#!/bin/sh

python manage.py migrate
python manage.py createsuperuser --username admin --email admin@example.com --noinput
python manage.py shell --command="from utils.db_entries import static_settings; static_settings()"