from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import LogEntry

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "decrypted_message")  # ✅ Show decrypted logs
    readonly_fields = ("timestamp", "decrypted_message")  # ✅ Prevent edits

    def decrypted_message(self, obj):
        """
        Display decrypted logs in the admin panel.
        """
        return obj.get_decrypted_message()

    decrypted_message.short_description = "Decrypted Log Message"

# ✅ Register LogEntry model
admin.site.register(LogEntry, LogEntryAdmin)
