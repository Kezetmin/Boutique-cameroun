from django.urls import path
from .views import (
    category_list_create,
    category_detail,
    product_list_create,
    product_detail,
    stock_entry,
    stock_movement_history,
)

urlpatterns = [
    # Catégories
    path('categories/', category_list_create, name='category_list_create'),
    path('categories/<int:category_id>/', category_detail, name='category_detail'),
  
  # Stock
    path('stock/entry/', stock_entry, name='stock_entry'),
    path('stock/history/', stock_movement_history, name='stock_movement_history'),

    # Produits
    path('', product_list_create, name='product_list_create'),
    path('<int:product_id>/', product_detail, name='product_detail'),
]