from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import Bag
from apps.products.serializers import BagSerializer

class CartItemSerializer(serializers.ModelSerializer):
    bag_details = BagSerializer(source='bag', read_only=True)
    total_price = serializers.ReadOnlyField()
    discount_amount = serializers.ReadOnlyField()
    original_total = serializers.ReadOnlyField()
    bag_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'bag', 'bag_details', 'quantity',
            'bag_price', 'total_price', 'discount_amount', 'original_total',
            'added_at', 'updated_at'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at']

class AddToCartSerializer(serializers.Serializer):
    bag_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1, max_value=99)
    
    def validate_bag_id(self, value):
        from apps.products.models import Bag
        try:
            bag = Bag.objects.get(id=value, is_active=True)
            if bag.stock < 1:
                raise serializers.ValidationError("Product is out of stock")
            return value
        except Bag.DoesNotExist:
            raise serializers.ValidationError("Product not found")

class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True, min_value=1, max_value=99)

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    total_discount = serializers.ReadOnlyField()
    total = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items', 'subtotal',
            'total_discount', 'total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']