from rest_framework import serializers
from .models import Table, Reservation, BillSplit, TableInvoice
from sale.models import SaleItem


class TableSerializer(serializers.ModelSerializer):
    """
    Serializer for table details.
    """
    class Meta:
        model = Table
        fields = "__all__"


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for handling reservations.
    """
    table_number = serializers.ReadOnlyField(source="table.table_number")

    class Meta:
        model = Reservation
        fields = [
            "id", "table", "table_number", "customer_name", "customer_email", 
            "reservation_time", "created_by", "created_at"
        ]
        read_only_fields = ["created_by", "created_at"]

    def validate(self, data):
        """
        Validate reservation time and prevent double booking.
        """
        table = data.get("table")
        reservation_time = data.get("reservation_time")

        if Reservation.objects.filter(table=table, reservation_time=reservation_time).exists():
            raise serializers.ValidationError("This table is already reserved for the selected time.")
        
        return data


class BillSplitSerializer(serializers.ModelSerializer):
    """
    Serializer for splitting bills.
    """
    sale_id = serializers.ReadOnlyField(source="sale.id")

    class Meta:
        model = BillSplit
        fields = [
            "id", "sale_id", "customer_name", "amount_paid", "payment_method", 
            "exchange_rate", "created_at"
        ]
        read_only_fields = ["created_at"]

    def validate_amount_paid(self, value):
        """
        Ensure amount paid is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Amount paid must be greater than zero.")
        return value


class SaleItemSerializer(serializers.ModelSerializer):
    """
    Serializer for sale items.
    """
    product_name = serializers.ReadOnlyField(source="product.name")
    sale_id = serializers.ReadOnlyField(source="sale.id")

    class Meta:
        model = SaleItem
        fields = [
            "id", "sale_id", "product", "product_name", "quantity", 
            "price_at_sale", "category", "routed_to", "created_at"
        ]
        read_only_fields = ["product_name", "routed_to", "created_at"]

    def validate_quantity(self, value):
        """
        Ensure quantity is at least 1.
        """
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class TableInvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for table invoices with SENIAT compliance.
    """
    table_number = serializers.ReadOnlyField(source="table.table_number")
    sale_id = serializers.ReadOnlyField(source="sale.id")
    control_code = serializers.ReadOnlyField()  # Control code is auto-generated
    tax_details = serializers.JSONField()

    class Meta:
        model = TableInvoice
        fields = [
            "id", "table", "table_number", "sale", "sale_id", "invoice_number", 
            "control_code", "total_amount", "tax_details", "pdf_file", "created_at"
        ]
        read_only_fields = ["invoice_number", "control_code", "total_amount", "pdf_file", "created_at"]

    def validate_tax_details(self, value):
        """
        Validate that tax details are correctly formatted.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Tax details must be a valid JSON object.")
        return value
