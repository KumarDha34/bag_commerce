from rest_framework import serializers
from .models import BankQR, Payment

class BankQRSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BankQR
        fields = ['id', 'name', 'bank_name', 'account_number', 'qr_code_image', 'qr_code_url', 'is_active']
        read_only_fields = ['id']
    
    def get_qr_code_url(self, obj):
        if obj.qr_code_image:
            return obj.qr_code_image.url
        return None

class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.ReadOnlyField(source='order.order_number')
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'amount', 'payment_method',
            'transaction_id', 'payment_screenshot', 'status', 
            'payment_date', 'verified_at', 'notes'
        ]
        read_only_fields = ['id', 'payment_date', 'verified_at', 'status']

class SubmitPaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)
    transaction_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    payment_screenshot = serializers.ImageField(required=False)
    payment_method = serializers.ChoiceField(choices=['bank_qr'], default='bank_qr')
    
    def validate(self, attrs):
        if not attrs.get('transaction_id') and not attrs.get('payment_screenshot'):
            raise serializers.ValidationError("Either transaction ID or payment screenshot is required")
        return attrs

class VerifyPaymentSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(choices=['verify', 'reject'], required=True)
    notes = serializers.CharField(required=False, allow_blank=True)