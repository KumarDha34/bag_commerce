from rest_framework import serializers
from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'full_name', 'email', 'phone', 'subject', 
            'message', 'status', 'admin_reply', 'replied_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'admin_reply', 'replied_at', 'created_at', 'updated_at']

class CreateContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'phone', 'subject', 'message']
    
    def validate_email(self, value):
        if '@' not in value or '.' not in value:
            raise serializers.ValidationError("Enter a valid email address")
        return value
    
    def validate_phone(self, value):
        if value and len(value) < 10:
            raise serializers.ValidationError("Enter a valid phone number")
        return value

class ReplyContactSerializer(serializers.Serializer):
    admin_reply = serializers.CharField(required=True)
    status = serializers.ChoiceField(choices=['replied', 'closed'], required=False, default='replied')