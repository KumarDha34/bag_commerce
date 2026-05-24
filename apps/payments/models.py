from django.db import models
from django.conf import settings
from apps.orders.models import Order

class BankQR(models.Model):
    """
    Store shop's bank QR code image
    """
    name = models.CharField(max_length=100, default='Bank QR Code')
    bank_name = models.CharField(max_length=100, help_text='Bank name (e.g., SBI, HDFC, ICICI)')
    account_number = models.CharField(max_length=50, blank=True, help_text='Account number (optional)')
    qr_code_image = models.ImageField(upload_to='bank_qr/', help_text='Upload your bank QR code screenshot')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bank_qr_codes'
    
    def __str__(self):
        return f"{self.bank_name} QR Code"

class Payment(models.Model):
    """
    Track customer payments
    """
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('verified', 'Payment Verified'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD = (
        ('bank_qr', 'Bank QR Code'),
        ('cod', 'Cash on Delivery'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='bank_qr')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_screenshot = models.ImageField(upload_to='payment_proof/', blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default='pending')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment for {self.order.order_number} - {self.status}"