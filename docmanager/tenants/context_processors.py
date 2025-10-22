"""
Context processor to make tenant available in templates.
"""

def tenant_context(request):
    """Add current tenant to template context."""
    return {
        'current_tenant': getattr(request, 'tenant', None)
    }