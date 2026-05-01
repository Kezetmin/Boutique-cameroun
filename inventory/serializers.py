from rest_framework import serializers
from .models import InventorySession, InventoryItem


class InventoryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    class Meta:
        model = InventoryItem
        fields = [
            'id',
            'product',
            'product_name',
            'system_stock',
            'real_stock',
            'difference',
            'note',
        ]


class InventorySessionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    items = InventoryItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = InventorySession
        fields = [
            'id',
            'title',
            'status',
            'note',
            'username',
            'validated_at',
            'created_at',
            'items',
        ]