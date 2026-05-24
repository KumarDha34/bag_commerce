from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator, RegexValidator
from django.core.mail import send_mail
from django.conf import settings
from .models import User, PasswordResetOTP
import random
import string
import re


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[EmailValidator(message="Enter a valid email address")]
    )
    phone = serializers.CharField(
        required=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Enter valid phone number")]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'phone', 'full_name', 'password', 'password2')
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value.lower()
    
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already registered")
        return value
    
    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password', '')
        
        try:
            user = User.objects.get(email=email)
            
            if not user.check_password(password):
                raise serializers.ValidationError("Invalid email or password")
            
            if not user.is_active:
                raise serializers.ValidationError("Account is disabled")
            
            attrs['user'] = user
            return attrs
            
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'phone', 'full_name', 'profile_picture','created_at', 'is_staff', 'is_superuser','is_active')
        read_only_fields = ('id', 'created_at', 'is_staff', 'is_superuser','is_staff','is_active')

        def get_profile_picture_url(self, obj):
            if obj.profile_picture:
                return obj.profile_picture.url
            return None

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        
        return attrs

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('full_name', 'phone','profile_picture')

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value)
            if not user.is_active:
                raise serializers.ValidationError("Account is disabled")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email")
        return value.lower()
    
    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email__iexact=email)
        
        otp = ''.join(random.choices(string.digits, k=6))
        
        PasswordResetOTP.objects.filter(email=email, is_used=False).delete()
        PasswordResetOTP.objects.create(email=email, otp=otp)
        
        subject = 'Password Reset Request - Bag E-commerce'
        message = f"""
        Hello {user.full_name or user.email},
        
        You requested to reset your password.
        
        Your OTP for password reset is: {otp}
        
        This OTP is valid for 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Bag E-commerce Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except:
            print(f"\n{'='*50}")
            print(f"PASSWORD RESET OTP FOR {email}: {otp}")
            print(f"{'='*50}\n")
        
        return True

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    
    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        otp = attrs.get('otp')
        
        try:
            user = User.objects.get(email__iexact=email)
            otp_record = PasswordResetOTP.objects.get(email=email, otp=otp, is_used=False)
            
            if not otp_record.is_valid():
                raise serializers.ValidationError("OTP has expired")
            
            attrs['user'] = user
            attrs['otp_record'] = otp_record
            
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email")
        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP")
        
        return attrs

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        
        email = attrs.get('email', '').lower()
        otp = attrs.get('otp')
        
        try:
            user = User.objects.get(email__iexact=email)
            otp_record = PasswordResetOTP.objects.get(email=email, otp=otp, is_used=False)
            
            if not otp_record.is_valid():
                raise serializers.ValidationError("OTP has expired")
            
            attrs['user'] = user
            attrs['otp_record'] = otp_record
            
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email")
        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP")
        
        return attrs
    
    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        otp_record = self.validated_data['otp_record']
        otp_record.is_used = True
        otp_record.save()
        
        subject = 'Password Reset Successful - Bag E-commerce'
        message = f"""
        Hello {user.full_name or user.email},
        
        Your password has been successfully reset.
        
        If you didn't perform this action, please contact support immediately.
        
        Best regards,
        Bag E-commerce Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except:
            print(f"Password reset confirmation email sent to {user.email}")
        
        return True