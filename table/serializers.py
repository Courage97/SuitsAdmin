from rest_framework import serializers
from .models import Table, Reservation

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = "__all__"

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = "__all__"

from rest_framework import serializers
from .models import BillSplit
from sale.models import SaleItem

class BillSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillSplit
        fields = ["id", "customer_name", "amount_paid", "payment_method", "created_at"]

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = "__all__"
