"""
Views for tenant management.
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Tenant


@staff_member_required
def tenant_list(request):
    """List all tenants (admin only)."""
    tenants = Tenant.objects.all()
    return render(request, 'tenants/list.html', {'tenants': tenants})