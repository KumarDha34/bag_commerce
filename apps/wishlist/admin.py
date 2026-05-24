from django.contrib import admin
from .models import Wishlist, WishlistItem

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_items', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def total_items(self, obj):
        return obj.items.count()
    total_items.short_description = 'Total Items'

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'wishlist', 'bag', 'added_at']
    list_filter = ['added_at']
    search_fields = ['wishlist__user__email', 'bag__name']