from django.urls import path
from .views import LogEventView, SecureLogListView

urlpatterns = [
    path("log-event/", LogEventView.as_view(), name="log-event"),
    path("logs/", SecureLogListView.as_view(), name="log-list"),
]
