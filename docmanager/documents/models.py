"""
Document management models with multi-tenant support and ACL.
"""
import hashlib
import os
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from tenants.models import Tenant


class TenantAwareManager(models.Manager):
    """
    Custom manager for SQLite tenant filtering.
    For PostgreSQL, schema isolation handles this automatically.
    """
    
    def get_queryset(self):
        qs = super().get_queryset()
        # Add tenant filtering for SQLite
        if not self._is_postgres() and hasattr(self, '_tenant'):
            return qs.filter(tenant=self._tenant)
        return qs
    
    def _is_postgres(self):
        return 'postgresql' in settings.DATABASES['default']['ENGINE']
    
    def for_tenant(self, tenant):
        """Set tenant for filtering."""
        self._tenant = tenant
        return self


class Role(models.Model):
    """User roles for permission management."""
    ADMIN = 'admin'
    EDITOR = 'editor'
    VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (EDITOR, 'Editor'),
        (VIEWER, 'Viewer'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='roles')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('tenant', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.role} @ {self.tenant.name}"


class Group(models.Model):
    """Groups for organizing users and permissions."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='document_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('tenant', 'name')
    
    def __str__(self):
        return f"{self.name} @ {self.tenant.name}"

class Folder(models.Model):
    """Hierarchical folder structure for organizing documents."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='subfolders')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = TenantAwareManager()
    
    class Meta:
        unique_together = ('tenant', 'parent', 'name')
        ordering = ['name']
    
    def __str__(self):
        return self.get_full_path()
    
    def get_full_path(self):
        """Get full path like /folder1/folder2/folder3"""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.name}"
        return f"/{self.name}"
    
    def get_ancestors(self):
        """Get list of ancestor folders from root to parent."""
        ancestors = []
        folder = self.parent
        while folder:
            ancestors.insert(0, folder)
            folder = folder.parent
        return ancestors


class FolderACL(models.Model):
    """Access Control List for folders."""
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'
    
    PERMISSION_CHOICES = [
        (READ, 'Read folder'),
        (WRITE, 'Create/upload in folder'),
        (DELETE, 'Delete folder'),
    ]
    
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='acls')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='granted_folder_acls')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['folder', 'user']),
            models.Index(fields=['folder', 'group']),
        ]

class StoredFile(models.Model):
    """
    Represents a physical file with checksum.
    Used for deduplication across tenants or per-tenant.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, 
                              related_name='stored_files', null=True, blank=True)
    checksum = models.CharField(max_length=64, db_index=True)  # SHA256
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = TenantAwareManager()
    
    class Meta:
        indexes = [
            models.Index(fields=['checksum']),
            models.Index(fields=['tenant', 'checksum']),
        ]
    
    def __str__(self):
        return f"{self.checksum[:16]}... ({self.file_size} bytes)"
    
    @staticmethod
    def compute_checksum(file_obj):
        """Compute SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        for chunk in file_obj.chunks():
            sha256.update(chunk)
        return sha256.hexdigest()


class Document(models.Model):
    """Document metadata with multi-tenant support."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='documents')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True,
                               related_name='documents')
    stored_file = models.ForeignKey(StoredFile, on_delete=models.CASCADE, 
                                    related_name='documents')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    original_filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    objects = TenantAwareManager()
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['tenant', 'title']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.title} @ {self.tenant.name}"


class ACL(models.Model):
    """Access Control List entries for documents."""
    READ = 'read'
    DOWNLOAD = 'download'
    EDIT = 'edit'
    DELETE = 'delete'
    
    PERMISSION_CHOICES = [
        (READ, 'Read metadata'),
        (DOWNLOAD, 'Download file'),
        (EDIT, 'Edit document'),
        (DELETE, 'Delete document'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='acls')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='granted_acls')
    
    class Meta:
        indexes = [
            models.Index(fields=['document', 'user']),
            models.Index(fields=['document', 'group']),
        ]
    
    def __str__(self):
        target = self.user.username if self.user else f"Group:{self.group.name}"
        return f"{target} - {self.permission} on {self.document.title}"


class AuditLog(models.Model):
    """Audit trail for document operations."""
    UPLOAD = 'upload'
    DOWNLOAD = 'download'
    VIEW = 'view'
    EDIT = 'edit'
    DELETE = 'delete'
    
    ACTION_CHOICES = [
        (UPLOAD, 'Upload'),
        (DOWNLOAD, 'Download'),
        (VIEW, 'View'),
        (EDIT, 'Edit'),
        (DELETE, 'Delete'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='audit_logs')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, 
                                related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)
    
    objects = TenantAwareManager()
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['document', 'action']),
        ]
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.action} - {self.timestamp}"