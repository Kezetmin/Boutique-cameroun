from django.contrib import admin
from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'monthly_price',
        'max_products',
        'max_users',
        'can_view_advanced_reports',
        'can_manage_customer_credits',
        'is_active',
    )
    list_filter = ('name', 'is_active')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'shop',
        'plan',
        'start_date',
        'end_date',
        'is_active',
    )
    list_filter = ('plan', 'is_active', 'end_date')
    search_fields = ('shop__name',)