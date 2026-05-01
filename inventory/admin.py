from django.contrib import admin
from .models import InventorySession, InventoryItem


class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    extra = 0


@admin.register(InventorySession)
class InventorySessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'shop', 'user', 'status', 'created_at', 'validated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'shop__name', 'user__username')
    inlines = [InventoryItemInline]


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'product', 'system_stock', 'real_stock', 'difference')
    search_fields = ('product__name',)