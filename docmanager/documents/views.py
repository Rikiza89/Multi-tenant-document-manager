"""
Views for document management.
"""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden, Http404
from django.db.models import Q
from .models import Document, AuditLog, ACL, Role, Folder, FolderACL
from .forms import DocumentUploadForm, DocumentSearchForm, FolderCreateForm
from .utils import validate_file, save_uploaded_file, get_client_ip
from .permissions import has_permission, get_user_documents, check_document_permission, check_folder_permission, has_folder_permission

def build_folder_tree(tenant, user):
    """Build hierarchical folder tree with permissions."""
    def build_tree(parent=None):
        folders = Folder.objects.filter(tenant=tenant, parent=parent)
        tree = []
        for folder in folders:
            if has_folder_permission(user, folder, FolderACL.READ):
                tree.append({
                    'folder': folder,
                    'children': build_tree(parent=folder)
                })
        return tree
    return build_tree()

def login_view(request):
    """Login view with tenant context."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('documents:list')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'documents/login.html')


def logout_view(request):
    """Logout view."""
    logout(request)
    return redirect('documents:login')


@login_required
def document_list(request):
    """List documents with search and filtering."""
    if not request.tenant:
        return HttpResponseForbidden("No tenant context available")
    
    form = DocumentSearchForm(request.GET)
    documents = get_user_documents(request.user, request.tenant)
    
    # Apply search filters
    if form.is_valid():
        query = form.cleaned_data.get('query')
        tags = form.cleaned_data.get('tags')
        
        if query:
            documents = documents.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(original_filename__icontains=query)
            )
        
        if tags:
            documents = documents.filter(tags__icontains=tags)
    
    return render(request, 'documents/list.html', {
        'documents': documents,
        'search_form': form
    })


@login_required
def document_upload(request, folder_id=None):
    """Upload document to folder."""
    if not request.tenant:
        return HttpResponseForbidden("No tenant context")
    
    folder = None
    if folder_id:
        folder = get_object_or_404(Folder, id=folder_id, tenant=request.tenant)
        if not has_folder_permission(request.user, folder, FolderACL.WRITE):
            return HttpResponseForbidden("No permission to upload here")
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, tenant=request.tenant)
        if form.is_valid():
            try:
                file_obj = request.FILES['file']
                validate_file(file_obj)
                stored_file = save_uploaded_file(file_obj, request.tenant)
                
                document = form.save(commit=False)
                document.tenant = request.tenant
                document.stored_file = stored_file
                document.uploaded_by = request.user
                document.original_filename = file_obj.name
                if folder:
                    document.folder = folder
                document.save()
                
                # Create ACL
                ACL.objects.create(document=document, user=request.user,
                                  permission=ACL.DOWNLOAD, granted_by=request.user)
                
                # Log
                AuditLog.objects.create(tenant=request.tenant, document=document,
                                       user=request.user, action=AuditLog.UPLOAD,
                                       ip_address=get_client_ip(request))
                
                messages.success(request, 'Document uploaded')
                if folder:
                    return redirect('documents:folder_list', folder_id=folder.id)
                return redirect('documents:list')
            except Exception as e:
                messages.error(request, f'Upload error: {str(e)}')
    else:
        initial = {'folder': folder} if folder else {}
        form = DocumentUploadForm(tenant=request.tenant, initial=initial)
    
    return render(request, 'documents/upload.html', {'form': form, 'folder': folder})


@login_required
def document_detail(request, document_id):
    """View document details and manage ACLs."""
    if not request.tenant:
        return HttpResponseForbidden("No tenant context available")
    
    document = get_object_or_404(Document, id=document_id, tenant=request.tenant)
    
    # Check read permission
    if not has_permission(request.user, document, ACL.READ):
        return HttpResponseForbidden("You don't have permission to view this document")
    
    # Log view
    AuditLog.objects.create(
        tenant=request.tenant,
        document=document,
        user=request.user,
        action=AuditLog.VIEW,
        ip_address=get_client_ip(request)
    )
    
    # Get ACLs
    acls = document.acls.all().select_related('user', 'group', 'granted_by')
    
    # Get audit logs
    logs = document.audit_logs.all().select_related('user')[:20]
    
    # Check permissions
    can_download = has_permission(request.user, document, ACL.DOWNLOAD)
    can_edit = has_permission(request.user, document, ACL.EDIT)
    can_delete = has_permission(request.user, document, ACL.DELETE)
    
    return render(request, 'documents/detail.html', {
        'document': document,
        'acls': acls,
        'logs': logs,
        'can_download': can_download,
        'can_edit': can_edit,
        'can_delete': can_delete
    })


@login_required
@check_document_permission(ACL.DOWNLOAD)
def document_download(request, document_id):
    """Download document file with permission check."""
    document = get_object_or_404(Document, id=document_id, tenant=request.tenant)
    
    # Log download
    AuditLog.objects.create(
        tenant=request.tenant,
        document=document,
        user=request.user,
        action=AuditLog.DOWNLOAD,
        ip_address=get_client_ip(request),
        details=f"Downloaded: {document.original_filename}"
    )
    
    # Stream file
    try:
        file_path = document.stored_file.file_path
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=document.stored_file.mime_type
        )
        response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
        return response
    except FileNotFoundError:
        raise Http404("File not found on disk")


@login_required
@check_document_permission(ACL.READ)
def document_preview(request, document_id):
    """Preview document in new tab."""
    document = get_object_or_404(Document, id=document_id, tenant=request.tenant)
    
    # Log view
    AuditLog.objects.create(
        tenant=request.tenant,
        document=document,
        user=request.user,
        action=AuditLog.VIEW,
        ip_address=get_client_ip(request),
        details=f"Previewed: {document.original_filename}"
    )
    
    file_path = document.stored_file.file_path
    mime_type = document.stored_file.mime_type
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise Http404("File not found")
    
    return render(request, 'documents/preview.html', {
        'document': document,
        'mime_type': mime_type,
        'can_download': has_permission(request.user, document, ACL.DOWNLOAD)
    })

@login_required
@check_document_permission(ACL.READ)
def document_preview_content(request, document_id):
    """Serve file content for preview (inline)."""
    document = get_object_or_404(Document, id=document_id, tenant=request.tenant)
    
    try:
        file_path = document.stored_file.file_path
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=document.stored_file.mime_type
        )
        response['Content-Disposition'] = f'inline; filename="{document.original_filename}"'
        return response
    except FileNotFoundError:
        raise Http404("File not found")

@login_required
@check_document_permission(ACL.DELETE)
def document_delete(request, document_id):
    """Delete a document."""
    document = get_object_or_404(Document, id=document_id, tenant=request.tenant)
    
    if request.method == 'POST':
        # Log deletion
        AuditLog.objects.create(
            tenant=request.tenant,
            document=document,
            user=request.user,
            action=AuditLog.DELETE,
            ip_address=get_client_ip(request),
            details=f"Deleted: {document.title}"
        )
        
        document.delete()
        messages.success(request, 'Document deleted successfully')
        return redirect('documents:list')
    
    return render(request, 'documents/delete_confirm.html', {'document': document})

@login_required
def folder_list(request, folder_id=None):
    """List folders and documents in current folder."""
    if not request.tenant:
        return HttpResponseForbidden("No tenant context")
    
    current_folder = None
    if folder_id:
        current_folder = get_object_or_404(Folder, id=folder_id, tenant=request.tenant)
        if not has_folder_permission(request.user, current_folder, FolderACL.READ):
            return HttpResponseForbidden("No permission to view this folder")
    
    # Get subfolders
    folders = Folder.objects.filter(tenant=request.tenant, parent=current_folder)
    folders = [f for f in folders if has_folder_permission(request.user, f, FolderACL.READ)]
    
    # Get documents
    documents = Document.objects.filter(tenant=request.tenant, folder=current_folder)
    documents = [d for d in documents if has_permission(request.user, d, ACL.READ)]
    
    # Breadcrumbs
    breadcrumbs = []
    if current_folder:
        breadcrumbs = current_folder.get_ancestors() + [current_folder]
    
    folder_tree = build_folder_tree(request.tenant, request.user)
        
    return render(request, 'documents/folder_list.html', {
        'current_folder': current_folder,
        'folders': folders,
        'documents': documents,
        'breadcrumbs': breadcrumbs,
        'folder_tree': folder_tree  # ADD THIS
    })

@login_required
def folder_create(request, parent_id=None):
    """Create a new folder."""
    if not request.tenant:
        return HttpResponseForbidden("No tenant context")
    
    parent = None
    if parent_id:
        parent = get_object_or_404(Folder, id=parent_id, tenant=request.tenant)
        if not has_folder_permission(request.user, parent, FolderACL.WRITE):
            return HttpResponseForbidden("No permission to create folders here")
    
    if request.method == 'POST':
        form = FolderCreateForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.tenant = request.tenant
            folder.created_by = request.user
            if parent:
                folder.parent = parent
            folder.save()
            
            # Grant creator full permissions
            for perm in [FolderACL.READ, FolderACL.WRITE, FolderACL.DELETE]:
                FolderACL.objects.create(
                    folder=folder, user=request.user,
                    permission=perm, granted_by=request.user
                )
            
            messages.success(request, f'Folder "{folder.name}" created')
            return redirect('documents:folder_list', folder_id=folder.id)
    else:
        form = FolderCreateForm(tenant=request.tenant, initial={'parent': parent})
    
    return render(request, 'documents/folder_create.html', {
        'form': form, 'parent': parent
    })

@login_required
@check_folder_permission(FolderACL.DELETE)
def folder_delete(request, folder_id):
    """Delete a folder."""
    folder = get_object_or_404(Folder, id=folder_id, tenant=request.tenant)
    
    if request.method == 'POST':
        parent_id = folder.parent.id if folder.parent else None
        folder.delete()
        messages.success(request, 'Folder deleted')
        if parent_id:
            return redirect('documents:folder_list', folder_id=parent_id)
        return redirect('documents:folder_list')
    
    return render(request, 'documents/folder_delete.html', {'folder': folder})