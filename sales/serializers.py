from rest_framework import serializers
from .models import Sale, SaleItem


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'unit_price',
            'subtotal',
            'created_at',
        ]
        read_only_fields = ['unit_price', 'subtotal', 'created_at']


class SaleSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    items = SaleItemSerializer(many=True, read_only=True)

    items_count = serializers.SerializerMethodField()
    total_profit = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id',
            'shop',
            'shop_name',
            'user',
            'username',
            'total_amount',
            'total_profit',
            'note',
            'items_count',
            'items',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'shop',
            'user',
            'total_amount',
            'total_profit',
            'created_at',
            'updated_at',
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_total_profit(self, obj):
        total = 0

        for item in obj.items.all():
            profit = (
                item.unit_price -
                item.product.purchase_price
            ) * item.quantity

            total += profit

        return total


class SaleCreateSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)

    items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )