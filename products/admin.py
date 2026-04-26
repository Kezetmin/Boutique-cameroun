from django.contrib import admin
from .models import Product, Category, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'shop', 'created_at')
    search_fields = ('name', 'shop__name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'shop',
        'purchase_price',
        'sale_price',
        'stock_quantity',
        'low_stock_threshold',
        'is_active',
        'created_at',
    )
    search_fields = ('name', 'shop__name')
    list_filter = ('is_active', 'shop',)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'shop',
        'product',
        'movement_type',
        'quantity',
        'user',
        'created_at',
    )
    list_filter = ('movement_type', 'shop', 'created_at')
    search_fields = ('product__name', 'shop__name', 'user__username')