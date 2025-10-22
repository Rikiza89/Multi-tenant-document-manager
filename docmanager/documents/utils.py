"""
Utility functions for document management.
"""
import os
import mimetypes
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import StoredFile


def validate_file(file_obj):
    """
    Validate uploaded file size and type.
    """
    # Check file size
    if file_obj.size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise ValidationError(f'File size exceeds maximum allowed size of {max_mb}MB')
    
    # Check file extension
    ext = os.path.splitext(file_obj.name)[1][1:].lower()
    if ext not in settings.ALLOWED_FILE_TYPES:
        raise ValidationError(
            f'File type not allowed. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}'
        )


def save_uploaded_file(file_obj, tenant):
    """
    Save uploaded file and return StoredFile instance.
    Handles deduplication based on checksum.
    """
    # Compute checksum
    checksum = StoredFile.compute_checksum(file_obj)
    file_obj.seek(0)  # Reset file pointer after reading
    
    # Check for duplicate based on TENANT_UNIQUENESS setting
    if settings.TENANT_UNIQUENESS == 'global':
        # Global uniqueness - check across all tenants
        existing = StoredFile.objects.filter(checksum=checksum).first()
    else:
        # Per-tenant uniqueness
        existing = StoredFile.objects.filter(checksum=checksum, tenant=tenant).first()
    
    if existing:
        # File already exists, return existing StoredFile
        return existing
    
    # Save new file
    mime_type = mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'
    
    # Create unique file path
    tenant_dir = os.path.join(settings.MEDIA_ROOT, 'files', tenant.schema_name)
    os.makedirs(tenant_dir, exist_ok=True)
    
    file_path = os.path.join(tenant_dir, f"{checksum}{os.path.splitext(file_obj.name)[1]}")
    
    # Write file to disk
    with open(file_path, 'wb+') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)
    
    # Create StoredFile record
    stored_file = StoredFile.objects.create(
        tenant=tenant if settings.TENANT_UNIQUENESS == 'per_tenant' else None,
        checksum=checksum,
        file_path=file_path,
        file_size=file_obj.size,
        mime_type=mime_type
    )
    
    return stored_file


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip