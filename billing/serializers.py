from rest_framework import serializers
from .models import ProformaInvoice

class ProformaInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInvoice
        fields = "__all__"
