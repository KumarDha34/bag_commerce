from django.urls import path
from .views import (
    GetBankQRView, GetBankQRImageView, SubmitPaymentView, PaymentStatusView,
    AdminBankQRManageView, AdminPendingPaymentsView, AdminVerifyPaymentView, AdminAllPaymentsView
)

urlpatterns = [
    # User endpoints
    path('bank-qr/', GetBankQRView.as_view(), name='bank-qr'),
    path('bank-qr-image/', GetBankQRImageView.as_view(), name='bank-qr-image'),
    path('submit/', SubmitPaymentView.as_view(), name='submit-payment'),
    path('status/<int:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
    # Admin endpoints
    path('admin/bank-qr/', AdminBankQRManageView.as_view(), name='admin-bank-qr'),
    path('admin/bank-qr/<int:qr_id>/', AdminBankQRManageView.as_view(), name='admin-bank-qr-detail'),
    path('admin/pending/', AdminPendingPaymentsView.as_view(), name='admin-pending-payments'),
    path('admin/verify/', AdminVerifyPaymentView.as_view(), name='admin-verify-payment'),
    path('admin/all/', AdminAllPaymentsView.as_view(), name='admin-all-payments'),
]