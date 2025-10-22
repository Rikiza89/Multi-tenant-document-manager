"""
Admin configuration for documents app.
"""
from django.contrib import admin
from .models import Role, Group, StoredFile, Document, ACL, AuditLog


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'created_at']
    list_filter = ['role', 'tenant']
    search_fields = ['user__username']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'created_at']
    list_filter = ['tenant']
    search_fields = ['name']


@admin.register(StoredFile)
class StoredFileAdmin(admin.ModelAdmin):
    list_display = ['checksum', 'tenant', 'file_size', 'mime_type', 'created_at']
    list_filter = ['tenant', 'mime_type']
    search_fields = ['checksum']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'tenant', 'uploaded_by', 'uploaded_at']
    list_filter = ['tenant', 'uploaded_at']
    search_fields = ['title', 'description']


@admin.register(ACL)
class ACLAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'group', 'permission', 'granted_at']
    list_filter = ['permission', 'document__tenant']
    search_fields = ['document__title', 'user__username']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'action', 'document', 'timestamp']
    list_filter = ['action', 'tenant', 'timestamp']
    search_fields = ['user__username', 'document__title']