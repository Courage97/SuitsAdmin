from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem
from inventory.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    price_at_purchase = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)  # ✅ Make read-only

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price_at_purchase"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # ✅ Nested serializer for order items

    class Meta:
        model = Order
        fields = ["id", "customer_name", "total_amount", "status", "created_by", "created_at", "items"]
        read_only_fields = ["total_amount", "created_by", "created_at"]

    def create(self, validated_data):
        """
        Manually create an order with nested order items.
        """
        items_data = validated_data.pop("items")  # ✅ Extract order items
        order = Order.objects.create(**validated_data)

        total_amount = Decimal(0)

        for item_data in items_data:
            product = item_data["product"]

            # ✅ Ensure product has enough stock
            if product.quantity_in_stock < item_data["quantity"]:
                raise serializers.ValidationError(f"Not enough stock for {product.name}")

            # ✅ Deduct stock
            product.quantity_in_stock -= item_data["quantity"]
            product.save()

            # ✅ Automatically set price_at_purchase using product's current price
            price_at_purchase = product.price  

            # ✅ Create order item with the correct price
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data["quantity"],
                price_at_purchase=price_at_purchase  # ✅ Now this is handled automatically
            )

            # ✅ Calculate total price using `price_at_purchase`
            total_amount += price_at_purchase * item_data["quantity"]

        # ✅ Save total amount after calculating
        order.total_amount = total_amount
        order.save()

        return order
