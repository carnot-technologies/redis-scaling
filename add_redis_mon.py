import django
django.setup()
from utils.db_entries import add_redis_settings

if __name__ == "__main__":
    add_redis_settings()
