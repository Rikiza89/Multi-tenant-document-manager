"""
URL patterns for tenant management.
"""
from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('list/', views.tenant_list, name='list'),
]