from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review
from apps.products.models import Bag

def update_product_rating(product):
    """Update average rating and review count for a product"""
    # Count ALL reviews (since all are auto-approved)
    all_reviews = Review.objects.filter(product=product)
    
    avg_rating = all_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    review_count = all_reviews.count()
    
    # Update the Bag model fields
    product.average_rating = round(avg_rating, 2)
    product.review_count = review_count
    product.save(update_fields=['average_rating', 'review_count'])
    print(f"Updated {product.name}: Rating={product.average_rating}, Count={product.review_count}")

@receiver(post_save, sender=Review)
def update_rating_on_save(sender, instance, **kwargs):
    """Update rating when a review is saved"""
    update_product_rating(instance.product)

@receiver(post_delete, sender=Review)
def update_rating_on_delete(sender, instance, **kwargs):
    """Update rating when a review is deleted"""
    update_product_rating(instance.product)