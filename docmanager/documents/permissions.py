"""
Permission checking utilities for documents.
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Document, ACL, Role


def check_document_permission(permission_type):
    """
    Decorator to check if user has specific permission on a document.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, document_id, *args, **kwargs):
            document = get_object_or_404(Document, id=document_id, tenant=request.tenant)
            
            if not has_permission(request.user, document, permission_type):
                return HttpResponseForbidden("You don't have permission to perform this action.")
            
            return view_func(request, document_id, *args, **kwargs)
        return wrapper
    return decorator


def has_permission(user, document, permission_type):
    """
    Check if user has specific permission on document.
    Checks: role-based permissions, per-file ACLs, and group memberships.
    """
    # Check if user is document owner
    if document.uploaded_by == user:
        return True
    
    # Check tenant admin role
    try:
        role = Role.objects.get(tenant=document.tenant, user=user)
        if role.role == Role.ADMIN:
            return True
        
        # Editors can read/download/edit
        if role.role == Role.EDITOR and permission_type in [ACL.READ, ACL.DOWNLOAD, ACL.EDIT]:
            return True
        
        # Viewers can read
        if role.role == Role.VIEWER and permission_type == ACL.READ:
            return True
    except Role.DoesNotExist:
        pass
    
    # Check direct ACL
    if ACL.objects.filter(document=document, user=user, permission=permission_type).exists():
        return True
    
    # Check group ACL
    user_groups = user.document_groups.filter(tenant=document.tenant)
    if ACL.objects.filter(document=document, group__in=user_groups, 
                         permission=permission_type).exists():
        return True
    
    return False


def get_user_documents(user, tenant):
    """
    Get all documents user has access to in a tenant.
    """
    from django.db.models import Q
    
    # Get user's role
    try:
        role = Role.objects.get(tenant=tenant, user=user)
        if role.role == Role.ADMIN:
            return Document.objects.filter(tenant=tenant)
    except Role.DoesNotExist:
        pass
    
    # Get documents via ACL and ownership
    user_groups = user.document_groups.filter(tenant=tenant)
    
    return Document.objects.filter(
        Q(tenant=tenant) & (
            Q(uploaded_by=user) |
            Q(acls__user=user) |
            Q(acls__group__in=user_groups)
        )
    ).distinct()