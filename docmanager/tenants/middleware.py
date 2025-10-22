"""
Middleware to resolve and set the current tenant based on request.
"""
from django.conf import settings
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse
from .models import Tenant


class TenantMiddleware:
    """
    Resolves tenant from subdomain or URL prefix.
    For PostgreSQL: sets search_path to tenant schema.
    For SQLite: stores tenant on request object for ORM filtering.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.is_postgres = 'postgresql' in settings.DATABASES['default']['ENGINE']
    
    def __call__(self, request):
        tenant = self.get_tenant_from_request(request)
        
        if tenant:
            request.tenant = tenant
            
            if self.is_postgres:
                # Set PostgreSQL schema for this request
                self.set_schema(tenant.schema_name)
        else:
            request.tenant = None
        
        response = self.get_response(request)
        
        if self.is_postgres and tenant:
            # Reset to public schema after request
            self.reset_schema()
        
        return response
    
    def get_tenant_from_request(self, request):
        """
        Extract tenant from subdomain or URL prefix.
        Example: tenant1.localhost:8000 or localhost:8000/t/tenant1/
        """
        # Skip tenant resolution for admin and static paths
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
        
        host = request.get_host().split(':')[0]
        
        # Try subdomain extraction (e.g., tenant1.localhost)
        parts = host.split('.')
        if len(parts) > 1 and parts[0] not in ['www', 'localhost', '127']:
            try:
                return Tenant.objects.get(domain=parts[0], is_active=True)
            except Tenant.DoesNotExist:
                pass
        
        # Try URL prefix extraction (e.g., /t/tenant1/)
        if request.path.startswith('/t/'):
            path_parts = request.path.split('/')
            if len(path_parts) > 2:
                try:
                    return Tenant.objects.get(domain=path_parts[2], is_active=True)
                except Tenant.DoesNotExist:
                    pass
        
        return None
    
    def set_schema(self, schema_name):
        """Set PostgreSQL search_path to tenant schema."""
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name}, public")
    
    def reset_schema(self):
        """Reset PostgreSQL search_path to public."""
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public")