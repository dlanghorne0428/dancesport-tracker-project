web: gunicorn dancesport_tracker.wsgi --log-file -
worker: celery -A 'dancesport_tracker' worker -l INFO
