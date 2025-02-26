from rest_framework import serializers
from .models import SecureLog


class SecureLogSerializer(serializers.ModelSerializer):
    decrypted_message = serializers.SerializerMethodField()

    class Meta:
        model = SecureLog
        fields = ["id", "event_type", "decrypted_message", "created_at"]

    def get_decrypted_message(self, obj):
        """
        Decrypts the log message before returning it.
        Only Admins should have access to this.
        """
        return obj.get_message()

