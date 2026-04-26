from django.urls import path
from .views import dashboard_stats, advanced_dashboard_stats

urlpatterns = [
    path('', dashboard_stats, name='dashboard_stats'),
    path('advanced/', advanced_dashboard_stats, name='advanced_dashboard_stats'),
]