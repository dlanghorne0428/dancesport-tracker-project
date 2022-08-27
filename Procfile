web: gunicorn dancesport_tracker.wsgi:application 
worker: celery -A 'dancesport_tracker' worker -l INFO
