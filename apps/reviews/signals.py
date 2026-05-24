from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review
from apps.products.models import Bag

def update_rating(product):
    reviews = Review.objects.filter(product=product, is_approved=True)
    product.average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    product.review_count = reviews.count()
    product.save()

@receiver(post_save, sender=Review)
def update_review_on_save(sender, instance, **kwargs):
    update_rating(instance.product)

@receiver(post_delete, sender=Review)
def update_review_on_delete(sender, instance, **kwargs):
    update_rating(instance.product)