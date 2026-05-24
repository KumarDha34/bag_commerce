from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import BagSerializer
class OrderItemSerializer(serializers.ModelSerializer):
    product_details = BagSerializer(source='product', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_details', 'product_name',
            'product_sku', 'product_price', 'quantity', 'total_price'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'full_name', 'email', 'phone',
            'address', 'subtotal', 'discount_amount', 'shipping_charge', 
            'total_amount', 'order_status', 'payment_status', 'items', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']

class CreateOrderSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    address = serializers.CharField()
    payment_method = serializers.ChoiceField(choices=['cod', 'bank_qr'], default='cod')

class UpdateOrderStatusSerializer(serializers.Serializer):
    order_status = serializers.ChoiceField(choices=[
        'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'
    ])