from rest_framework import serializers
from .models import Wishlist, WishlistItem
from apps.products.models import Bag
from apps.products.serializers import BagSerializer

class WishlistItemSerializer(serializers.ModelSerializer):
    bag_details = BagSerializer(source='bag', read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = ['id', 'bag', 'bag_details', 'added_at']
        read_only_fields = ['id', 'added_at']

class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    
    class Meta:
        model = Wishlist
        fields = ['id', 'items', 'total_items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AddToWishlistSerializer(serializers.Serializer):
    bag_id = serializers.IntegerField(required=True)
    
    def validate_bag_id(self, value):
        try:
            bag = Bag.objects.get(id=value, is_active=True)
            return value
        except Bag.DoesNotExist:
            raise serializers.ValidationError("Product not found")