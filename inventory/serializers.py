from rest_framework import serializers
from .models import Product, StockMovement, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )  

    class Meta:
        model = Product
        fields = '__all__'


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ('created_by',)  # Ensure users can't manually set this field

    def create(self, validated_data):
        """
        Automatically assign the logged-in user as `created_by`.
        """
        request = self.context.get('request')  # Get request context
        if request and request.user:
            validated_data['created_by'] = request.user  # Assign the user
        return super().create(validated_data)