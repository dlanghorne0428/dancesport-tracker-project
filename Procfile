web: python manage.py migrate && gunicorn dancesport_tracker.wsgi
worker: celery -A 'dancesport_tracker' worker -l INFO
