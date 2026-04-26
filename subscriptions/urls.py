from django.urls import path
from .views import (
    plan_list,
    my_subscription,
    activate_subscription,
    deactivate_subscription,
)

urlpatterns = [
    path('plans/', plan_list, name='plan_list'),
    path('my-subscription/', my_subscription, name='my_subscription'),
    path('activate/', activate_subscription, name='activate_subscription'),
    path('deactivate/', deactivate_subscription, name='deactivate_subscription'),
]