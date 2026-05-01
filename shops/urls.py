from django.urls import path
from .views import create_shop, my_shop, reset_demo_data, shop_member_list_create, shop_member_detail

urlpatterns = [
    path('create/', create_shop, name='create_shop'),
    path('my-shop/', my_shop, name='my_shop'),

    path('members/', shop_member_list_create, name='shop_member_list_create'),
    path(
    'demo-reset/',
    reset_demo_data,
    name='reset_demo_data'
),
    path('members/<int:member_id>/', shop_member_detail, name='shop_member_detail'),
]