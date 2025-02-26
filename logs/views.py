from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminUser
from .models import SecureLog
from .serializers import SecureLogSerializer
from django.utils.timezone import now


class LogEventView(APIView):
    """
    API endpoint to create secure logs.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        event_type = request.data.get("event_type", "General")
        message = request.data.get("message", "")

        log_entry = SecureLog(event_type=event_type)
        log_entry.set_message(message)
        log_entry.save()

        return Response({"message": "Log saved securely!"})


class SecureLogListView(generics.ListAPIView):
    """
    Retrieve system logs (Admin only).
    Supports filtering by event type and date.
    """
    queryset = SecureLog.objects.all().order_by("-created_at")
    serializer_class = SecureLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["event_type"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        """
        Filter logs by event type or date if query params are provided.
        """
        queryset = super().get_queryset()
        event_type = self.request.query_params.get("event_type")
        date = self.request.query_params.get("date")

        if event_type:
            queryset = queryset.filter(event_type__icontains=event_type)
        if date:
            queryset = queryset.filter(created_at__date=date)

        return queryset


def log_security_event(event_type, message):
    """
    Automatically log security events such as failed logins or permission changes.
    """
    SecureLog.objects.create(event_type=event_type, encrypted_message=message)
