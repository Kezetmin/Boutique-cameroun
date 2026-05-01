from django.urls import path
from .views import (
    start_inventory,
    update_inventory_item,
    validate_inventory,
    inventory_list,
    inventory_detail,
)

urlpatterns = [
    path('', inventory_list, name='inventory_list'),
    path('start/', start_inventory, name='start_inventory'),
    path('<int:session_id>/', inventory_detail, name='inventory_detail'),
    path('<int:session_id>/validate/', validate_inventory, name='validate_inventory'),
    path(
    'items/<int:item_id>/',
    update_inventory_item,
    name='update_inventory_item'
),
]