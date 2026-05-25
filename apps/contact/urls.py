from django.urls import path
from .views import (
    SubmitContactView,
    AdminContactListView,
    AdminContactDetailView,
    AdminContactStatsView
)

urlpatterns = [
    # Public endpoints
    path('submit/', SubmitContactView.as_view(), name='submit-contact'),
    
    # Admin endpoints
    path('admin/messages/', AdminContactListView.as_view(), name='admin-contact-list'),
    path('admin/messages/<int:message_id>/', AdminContactDetailView.as_view(), name='admin-contact-detail'),
    path('admin/stats/', AdminContactStatsView.as_view(), name='admin-contact-stats'),
]