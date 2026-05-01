from django.urls import path
from .views import customer_list_create, customer_detail

urlpatterns = [
    path('', customer_list_create, name='customer_list_create'),
    path('<int:customer_id>/', customer_detail, name='customer_detail'),
]