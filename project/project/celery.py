from __future__ import absolute_import

import os
from celery import Celery
from celery.utils.log import get_task_logger
from django.conf import settings

logger = get_task_logger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# app = Celery('testmq',broker=settings.BROKER_URL,backend=settings.BROKER_URL)
app = Celery("project")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
