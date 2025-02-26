from django.db import models
from .utils import encrypt_data, decrypt_data

class SecureLog(models.Model):
    """
    Stores encrypted log entries.
    """
    event_type = models.CharField(max_length=100)
    encrypted_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def set_message(self, message):
        """Encrypt and store the message"""
        self.encrypted_message = encrypt_data(message)

    def get_message(self):
        """Decrypt and return the stored message"""
        return decrypt_data(self.encrypted_message)

    def __str__(self):
        return f"{self.event_type} - {self.created_at}"



class LogEntry(models.Model):
    """
    Stores system logs with AES-256 encryption.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    encrypted_message = models.BinaryField()  # ✅ Store encrypted logs

    def set_message(self, message):
        """
        Encrypts and stores the message.
        """
        self.encrypted_message = encrypt_data(message)
        self.save()

    def get_decrypted_message(self):
        """
        Decrypts the stored message for Admin Panel viewing.
        """
        return decrypt_data(self.encrypted_message)

    def __str__(self):
        return f"Log Entry - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

