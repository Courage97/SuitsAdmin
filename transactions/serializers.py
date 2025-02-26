from rest_framework import serializers
from .models import Invoice, ExchangeRate, SalesReport

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'

    def create(self, validated_data):
        """
        Convert amount based on selected currency and save invoice.
        """
        currency = validated_data.get("currency", "USD")
        total_amount = validated_data.get("total_amount")

        # Default to USD if no conversion needed
        converted_amount = total_amount
        exchange_rate = 1.0

        # Get exchange rate if not USD
        if currency != "USD":
            try:
                rate_obj = ExchangeRate.objects.get(target_currency=currency)
                exchange_rate = rate_obj.rate
                converted_amount = total_amount * exchange_rate
            except ExchangeRate.DoesNotExist:
                raise serializers.ValidationError({"error": f"Exchange rate for {currency} not found."})

        validated_data["converted_amount"] = converted_amount
        validated_data["exchange_rate"] = exchange_rate
        return super().create(validated_data)

class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = "__all__"

class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = "__all__"
