from django.contrib import admin
from .models import Shop ,ShopMember

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner_name', 'phone', 'address', 'user', 'created_at')
    search_fields = ('name', 'owner_name', 'phone')


@admin.register(ShopMember)
class ShopMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'shop')
    search_fields = ('shop__name', 'user__username')