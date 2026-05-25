from django.db import models
from django.conf import settings

class ContactMessage(models.Model):
    """
    Contact message from website visitors
    """
    SUBJECT_CHOICES = (
        ('Customer Support', 'Customer Support'),
        ('Order Inquiry', 'Order Inquiry'),
        ('Product Information', 'Product Information'),
        ('Return/Refund', 'Return/Refund'),
        ('Wholesale Inquiry', 'Wholesale Inquiry'),
        ('Custom Order', 'Custom Order'),
        ('Feedback', 'Feedback'),
        ('Other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    )
    
    # Contact information
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    
    # Admin fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='replied_messages'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_messages'
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.full_name} - {self.subject} - {self.created_at.strftime('%Y-%m-%d')}"