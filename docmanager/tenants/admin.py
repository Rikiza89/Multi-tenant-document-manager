"""
Admin configuration for tenants app.
"""
from django.contrib import admin
from .models import Tenant, TenantUser


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'domain', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'domain']


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'is_tenant_admin', 'joined_at']
    list_filter = ['is_tenant_admin', 'tenant']
    search_fields = ['user__username', 'tenant__name']