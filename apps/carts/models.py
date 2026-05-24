from django.db import models
from django.conf import settings
from apps.products.models import Bag

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carts'
        ordering = ['-created_at']
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Get subtotal without discounts"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_discount(self):
        """Get total discount amount"""
        return sum(item.discount_amount for item in self.items.all())
    
    @property
    def total(self):
        """Get final total after discount"""
        return self.subtotal
    
    def __str__(self):
        if self.user:
            return f"Cart of {self.user.email}"
        return f"Cart - Session: {self.session_key}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    bag = models.ForeignKey(Bag, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'bag']
        ordering = ['-added_at']
    
    @property
    def bag_price(self):
        """Get current bag price (with discount)"""
        return self.bag.final_price
    
    @property
    def total_price(self):
        """Get total price for this item"""
        return self.quantity * self.bag_price
    
    @property
    def discount_amount(self):
        """Get discount amount for this item"""
        if self.bag.discount_price:
            original_total = self.quantity * self.bag.price
            discounted_total = self.quantity * self.bag.discount_price
            return original_total - discounted_total
        return 0
    
    @property
    def original_total(self):
        """Get original total without discount"""
        return self.quantity * self.bag.price
    
    def __str__(self):
        return f"{self.quantity} x {self.bag.name}"