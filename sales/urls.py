from django.urls import path
from .views import sale_list_create, sale_detail, sales_history

urlpatterns = [
    path('', sale_list_create, name='sale_list_create'),
    path('history/', sales_history, name='sales_history'),
    path('<int:sale_id>/', sale_detail, name='sale_detail'),
]