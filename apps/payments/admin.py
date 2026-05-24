from django.contrib import admin
from .models import Payment, BankQR
# Register your models here.


admin.site.register(Payment)
admin.site.register(BankQR)