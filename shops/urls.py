from django.urls import path
from .views import create_shop, my_shop

urlpatterns = [
    path('create/', create_shop, name='create_shop'),
    path('my-shop/', my_shop, name='my_shop'),
]