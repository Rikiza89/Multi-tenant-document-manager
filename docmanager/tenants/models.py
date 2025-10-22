"""
Tenant model for multi-tenancy support.
"""
from django.db import models
from django.contrib.auth.models import User


class Tenant(models.Model):
    """
    Represents a tenant in the system.
    For PostgreSQL: schema_name is used to create separate schemas.
    For SQLite: tenant_id is used for filtering.
    """
    name = models.CharField(max_length=100, unique=True)
    schema_name = models.CharField(max_length=63, unique=True, 
                                   help_text="PostgreSQL schema name or identifier")
    domain = models.CharField(max_length=255, unique=True, 
                             help_text="Subdomain or URL prefix for tenant")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TenantUser(models.Model):
    """
    Links users to tenants for multi-tenant access.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tenant_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
    is_tenant_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('tenant', 'user')
        ordering = ['tenant', 'user']
    
    def __str__(self):
        return f"{self.user.username} @ {self.tenant.name}"
