from django.urls import path
from .views import cash_summary, sale_list_create, sale_detail, sale_receipt, sales_history
from .views import sale_list_create, sale_detail, sales_history, cancel_sale, add_sale_payment,sales_debts

urlpatterns = [
    path('', sale_list_create, name='sale_list_create'),
    path('history/', sales_history, name='sales_history'),
    path('debts/', sales_debts, name='sales_debts'),
    path('cash-summary/', cash_summary, name='cash_summary'),
    path('<int:sale_id>/receipt/', sale_receipt, name='sale_receipt'),
    path('<int:sale_id>/cancel/', cancel_sale, name='cancel_sale'),
    path('<int:sale_id>/add-payment/', add_sale_payment, name='add_sale_payment'),
    path('<int:sale_id>/', sale_detail, name='sale_detail'),
]