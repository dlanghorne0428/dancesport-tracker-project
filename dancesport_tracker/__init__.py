from __future__ import absolute_import, unicode_literals
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

logger.info("Starting Celery app")

__all__ = ('celery_app',)
