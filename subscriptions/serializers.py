from django.utils import timezone

from rest_framework import serializers
from .models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id',
            'name',
            'name_display',
            'monthly_price',
            'description',
            'max_products',
            'max_users',
            'can_view_advanced_reports',
            'can_manage_customer_credits',
            'is_active',
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.get_name_display', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    is_valid = serializers.SerializerMethodField()
    has_expired = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    def get_days_remaining(self, obj):
        today = timezone.localdate()

        if obj.end_date < today:
            return 0

        return (obj.end_date - today).days

    class Meta:
        model = Subscription
        fields = [
            'id',
            'shop_name',
            'plan',
            'plan_name',
            'days_remaining',
            'is_trial',
            'start_date',
            'end_date',
            'status',
            'is_active',
            'is_valid',
            'has_expired',
            'created_at',
            'updated_at',
        ]

    def get_is_valid(self, obj):
        obj.refresh_status()
        return obj.is_valid()

    def get_has_expired(self, obj):
        return obj.has_expired()
    
    def get_days_remaining(self, obj):
        today = timezone.localdate()

        if obj.end_date < today:
            return 0

        return (obj.end_date - today).days