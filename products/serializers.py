from rest_framework import serializers
from .models import Product, Category
from .models import Product, Category, StockMovement


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'description',
            'products_count',
            'created_at',
        ]

    def get_products_count(self, obj):
        return obj.products.count()

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom de la catégorie est obligatoire.")
        return value.strip()


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer principal du produit.
    """

    is_low_stock = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'purchase_price',
            'sale_price',
            'stock_quantity',
            'low_stock_threshold',
            'category',
            'category_name',
            'is_low_stock',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def get_is_low_stock(self, obj):
        return obj.is_low_stock()

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def validate_purchase_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix d'achat doit être supérieur à 0.")
        return value

    def validate_sale_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix de vente doit être supérieur à 0.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif.")
        return value

    def validate_low_stock_threshold(self, value):
        if value < 0:
            raise serializers.ValidationError("Le seuil de stock faible ne peut pas être négatif.")
        return value
    

class StockMovementSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'historique des mouvements de stock.
    """

    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    movement_type_display = serializers.CharField(
        source='get_movement_type_display',
        read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            'id',
            'shop_name',
            'product',
            'product_name',
            'username',
            'movement_type',
            'movement_type_display',
            'quantity',
            'note',
            'supplier',
            'created_at',
        ]
        read_only_fields = [
            'shop_name',
            'product_name',
            'username',
            'movement_type_display',
            'created_at',
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être supérieure à 0.")
        return value