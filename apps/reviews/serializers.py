from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Review
        fields = [
            'id',
            'product',
            'user',
            'user_name',
            'user_email',
            'rating',
            'comment',
            'is_approved',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'is_approved']


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['product', 'rating', 'comment']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if not request:
            return attrs

        user = request.user
        product = attrs.get('product')

        # Allow update case (VERY IMPORTANT FIX)
        if self.instance:
            return attrs

        # Prevent duplicate review per user per product
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError(
                "You have already reviewed this product"
            )

        return attrs