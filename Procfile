web: gunicorn wsgi:app
worker: celery -A celery_worker worker --loglevel=info 