from django.db import models
from django.conf import settings
from apps.products.models import Bag

class Wishlist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wishlists'
        ordering = ['-created_at']
    
    @property
    def total_items(self):
        return self.items.count()
    
    def __str__(self):
        return f"Wishlist of {self.user.email}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    bag = models.ForeignKey(Bag, on_delete=models.CASCADE, related_name='wishlist_items')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wishlist_items'
        unique_together = ['wishlist', 'bag']  
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.bag.name} in {self.wishlist.user.email}'s wishlist"