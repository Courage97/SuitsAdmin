import os
from celery import Celery

# Ensure the correct Django settings module is used
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Suitadmin.settings")  # ✅ Fix capitalization!

app = Celery("Suitadmin")  # ✅ Use the correct project name
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
