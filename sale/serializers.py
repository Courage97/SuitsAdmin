from rest_framework import serializers
from decimal import Decimal
from .models import Sale, SaleItem, ExchangeRate, Invoice

class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    price_at_sale = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "quantity", "price_at_sale"]

    def validate_quantity(self, value):
        """ Ensure quantity is positive. """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = ["id", "customer_name", "total_amount", "status", "created_by", "created_at", "items"]
        read_only_fields = ["total_amount", "created_by", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        if not items_data:
            raise serializers.ValidationError("At least one item is required to create a sale.")

        sale = Sale.objects.create(**validated_data)
        total_amount = Decimal(0)

        for item_data in items_data:
            product = item_data["product"]

            if product.quantity_in_stock < item_data["quantity"]:
                raise serializers.ValidationError(f"Not enough stock for {product.name}")

            product.quantity_in_stock -= item_data["quantity"]
            product.save()

            price_at_sale = product.price
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item_data["quantity"],
                price_at_sale=price_at_sale
            )

            total_amount += price_at_sale * item_data["quantity"]

        sale.total_amount = total_amount
        sale.save()
        return sale

    def validate_items(self, value):
        """ Ensure items list is not empty. """
        if not value:
            raise serializers.ValidationError("A sale must contain at least one item.")
        return value


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = "__all__"


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"

    def create(self, validated_data):
        sale = validated_data.get("sale")
        
        if sale.status != "completed":
            raise serializers.ValidationError({"error": "Invoice can only be generated for completed sales."})

        currency = validated_data.get("currency", "USD")
        total_amount = validated_data.get("total_amount")
        converted_amount = total_amount
        exchange_rate = 1.0

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
