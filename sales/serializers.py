from rest_framework import serializers
from .models import Sale, SaleItem
from .models import Sale, SaleItem, SalePayment


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

class SalePaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SalePayment
        fields = [
            'id',
            'sale',
            'customer',
            'customer_name',
            'amount',
            'note',
            'username',
            'created_at',
        ]


class SaleSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    total_profit = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    payments = SalePaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id',
            'receipt_number',
            'shop',
            'shop_name',
            'user',
            'username',
            'total_amount',
            'note',
            'status',
            'cancel_reason',
            'cancelled_at',
            'total_profit',
            'items_count',
            'items',
            'created_at',
            'updated_at',
            'customer',
            'customer_name',
            'amount_paid',
            'remaining_amount',
            'payment_status',
            'payments',
        ]

        read_only_fields = [
            'shop',
            'user',
            'receipt_number',
            'total_amount',
            'total_profit',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancel_reason',
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
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer = serializers.IntegerField(required=False, allow_null=True)
    amount_paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=0
    )
    items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Une vente doit contenir au moins un produit.")
        return value

    def validate_amount_paid(self, value):
        if value < 0:
            raise serializers.ValidationError("Le montant payé ne peut pas être négatif.")
        return value


class AddSalePaymentSerializer(serializers.Serializer):
    """
    Serializer pour ajouter un paiement à une vente existante.
    """
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant du paiement doit être supérieur à 0.")
        return value