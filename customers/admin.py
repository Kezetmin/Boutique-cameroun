from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'shop', 'created_at')
    search_fields = ('name', 'phone', 'shop__name')
    list_filter = ('shop', 'created_at')