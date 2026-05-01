from django.contrib import admin
from .models import Sale, SaleItem
from .models import Sale, SaleItem, SalePayment

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'user', 'total_amount', 'created_at','payment_status', 'status', 'customer','amount_paid', 'remaining_amount')
    search_fields = ('shop__name', 'user__username')
    list_filter = ('shop', 'created_at')
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'product', 'quantity', 'unit_price', 'subtotal', 'created_at')
    search_fields = ('product__name',)
    list_filter = ('created_at',)

@admin.register(SalePayment)
class SalePaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'customer', 'amount', 'user', 'created_at')
    search_fields = ('sale__id', 'customer__name', 'user__username')
    list_filter = ('shop', 'created_at')