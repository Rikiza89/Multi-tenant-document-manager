"""
Views for document management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden, Http404
from django.db.models import Q
from .models import Document, AuditLog, ACL, Role
from .forms import DocumentUploadForm, DocumentSearchForm
from .utils import validate_file, save_uploaded_file, get_client_ip
from .permissions import has_permission, get_user_documents, check_document_permission


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
def document_upload(request):
    """Upload a new document."""
    if not request.tenant:
        return HttpResponseForbidden("No tenant context available")
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Validate file
                file_obj = request.FILES['file']
                validate_file(file_obj)
                
                # Save file
                stored_file = save_uploaded_file(file_obj, request.tenant)
                
                # Create document
                document = form.save(commit=False)
                document.tenant = request.tenant
                document.stored_file = stored_file
                document.uploaded_by = request.user
                document.original_filename = file_obj.name
                document.save()
                
                # Create ACL entry for uploader
                ACL.objects.create(
                    document=document,
                    user=request.user,
                    permission=ACL.DOWNLOAD,
                    granted_by=request.user
                )
                
                # Log upload
                AuditLog.objects.create(
                    tenant=request.tenant,
                    document=document,
                    user=request.user,
                    action=AuditLog.UPLOAD,
                    ip_address=get_client_ip(request),
                    details=f"Uploaded: {document.original_filename}"
                )
                
                messages.success(request, 'Document uploaded successfully')
                return redirect('documents:detail', document_id=document.id)
                
            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below')
    else:
        form = DocumentUploadForm()
    
    return render(request, 'documents/upload.html', {'form': form})


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