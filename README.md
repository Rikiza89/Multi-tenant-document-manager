# Multi-Tenant Document Management System

A Django-based document management system with multi-tenant architecture, supporting both SQLite (development) and PostgreSQL (production) databases.

## Features

- **Multi-Tenant Architecture**: Shared database with tenant isolation
  - PostgreSQL: Schema-based separation
  - SQLite: Tenant ID-based filtering
- **Hierarchical Folder Management**: Multi-level folder organization with collapsible tree view
- **Document Management**: Upload, search, view metadata, and download documents
- **Advanced Preview System**: In-browser preview for 40+ file types
  - PDFs, images, videos, audio
  - Code files with syntax highlighting (Python, JS, Java, etc.)
  - Office documents (Word, Excel, PowerPoint)
  - 3D models (STL, OBJ)
  - Text files, JSON, XML, YAML, Markdown
- **Access Control**: Multi-level permissions (roles, groups, per-folder/file ACLs)
- **File Deduplication**: SHA256 checksum-based duplicate detection
- **Audit Logging**: Complete audit trail of all document operations
- **Responsive UI**: Clean, minimal interface with interactive tree navigation
- **Security**: File validation, permission enforcement, CSRF protection

## Requirements

- Python 3.11+ (tested with python 3.11.9)
- Django 4.2+ (tested with Django 5.2.5) 
- PostgreSQL (for production) or SQLite (for development)


**Project Structure**:
```
📁 docmanager
├── 📁 docmanager
│   ├── 🐍 __init__.py
│   ├── 🐍 asgi.py
│   ├── 🐍 settings.py
│   ├── 🐍 urls.py
│   └── 🐍 wsgi.py
├── 📁 documents
│   ├── 📁 migrations
│   │   └── 🐍 __init__.py
│   ├── 🐍 __init__.py
│   ├── 🐍 admin.py
│   ├── 🐍 apps.py
│   ├── 🐍 forms.py
│   ├── 🐍 models.py
│   ├── 🐍 permissions.py
│   ├── 🐍 tests.py
│   ├── 🐍 urls.py
│   ├── 🐍 utils.py
│   └── 🐍 views.py
├── 📁 media
├── 📁 static
│   └── 📁 css
│       └── 🎨 style.css
├── 📁 templates
│   ├── 📁 documents
│   │   ├── 🌐 delete_confirm.html
│   │   ├── 🌐 detail.html
│   │   ├── 🌐 folder_create.html
│   │   ├── 🌐 folder_list.html
│   │   ├── 🌐 folder_tree.html
│   │   ├── 🌐 folder_tree_recursive.html
│   │   ├── 🌐 list.html
│   │   ├── 🌐 login.html
│   │   ├── 🌐 preview.html
│   │   └── 🌐 upload.html
│   ├── 📁 tenants
│   │   └── 🌐 list.html
│   └── 🌐 base.html
├── 📁 tenants
│   ├── 📁 management
│   │   ├── 📁 commands
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 create_tenant.py
│   │   └── 🐍 __init__.py
│   ├── 📁 migrations
│   │   └── 🐍 __init__.py
│   ├── 🐍 __init__.py
│   ├── 🐍 admin.py
│   ├── 🐍 apps.py
│   ├── 🐍 context_processors.py
│   ├── 🐍 middleware.py
│   ├── 🐍 models.py
│   ├── 🐍 tests.py
│   ├── 🐍 urls.py
│   └── 🐍 views.py
├── ⚙️ .env.example
├── 🐍 manage.py
└── 📄 requirements.txt
```

## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd docmanager
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

**SQLite (Development)**:
```env
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.localhost
TENANT_UNIQUENESS=global
MAX_UPLOAD_SIZE=52428800
ALLOWED_FILE_TYPES=pdf,doc,docx,txt,rtf,odt,csv,xls,xlsx,ppt,pptx,md,json,yaml,xml,png,jpg,jpeg,gif,svg,mp3,mp4,py,js,html,css,sql,java,cpp,c,go,rs,php
```

**PostgreSQL (Production)**:
```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=docmanager
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,.yourdomain.com
```

### 3. Initialize Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Create Tenants

```bash
python manage.py create_tenant "Company A" --domain=companya
python manage.py create_tenant "Company B" --domain=companyb
```

### 5. Setup Users

Access admin at `http://localhost:8000/admin/`:
1. Create users (Authentication > Users)
2. Link to tenants (Tenants > Tenant users)
3. Assign roles (Documents > Roles)

### 6. Run Application

```bash
python manage.py runserver
```

Access: `http://companya.localhost:8000`

## Usage Guide

### Folder Management

**Creating Folders**:
- Navigate to parent folder or root
- Click "+ Folder"
- Enter name and submit
- Appears in tree view sidebar

**Navigation**:
- **Tree View**: Collapsible sidebar shows full hierarchy
- **Breadcrumbs**: Path navigation at top
- **Main Area**: Grid view of folders and files

**Folder Permissions** (inherited by children):
- **Read**: View folder contents
- **Write**: Create subfolders and upload files
- **Delete**: Remove folder

### Document Management

**Uploading**:
1. Navigate to target folder
2. Click "+ Upload"
3. Select folder (if applicable)
4. Fill metadata: title, description, tags
5. Choose file
6. Submit

**Previewing Documents**:
- Click "👁 Preview" button to open in new tab
- Supports 40+ file types:
  - **PDFs**: Native browser viewer
  - **Images**: PNG, JPG, GIF, SVG, WebP, TIFF
  - **Videos**: MP4, WebM, MKV, AVI, MOV
  - **Audio**: MP3, WAV, OGG, FLAC
  - **Code**: Python, JavaScript, TypeScript, Java, C++, Go, Rust, PHP, SQL (with syntax highlighting)
  - **Office**: Word, Excel, PowerPoint (via Office Online)
  - **3D Models**: STL, OBJ (interactive Three.js viewer)
  - **Text**: TXT, MD, JSON, XML, YAML, CSV, HTML, CSS
  - **Notebooks**: Jupyter (.ipynb)

**Search & Filter**:
- Search by title, description, filename
- Filter by tags
- Navigate via tree view

### Access Control

**Four-Level Permission System**:

1. **Roles (Tenant-Wide)**:
   - Admin: Full access
   - Editor: Read, download, edit
   - Viewer: Read-only

2. **Folder ACLs**:
   - Read, Write, Delete
   - Inherited by subfolders

3. **Document ACLs**:
   - Read, Download, Edit, Delete
   - Per-file granular control

4. **Groups**: Collective permission assignment

### File Deduplication

- **Global mode**: Prevents duplicates across tenants
- **Per-tenant mode**: Allows duplicates per tenant
- SHA256 checksum-based detection

## Multi-Tenancy Implementation

**PostgreSQL**: Schema-based isolation
```sql
SET search_path TO tenant1, public;
```

**SQLite**: ORM-level filtering (development only)
```python
Document.objects.filter(tenant=current_tenant)
```

## Project Structure

```
docmanager/
├── docmanager/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tenants/
│   ├── models.py          # Tenant, TenantUser
│   ├── middleware.py      # Tenant resolution
│   └── management/commands/create_tenant.py
├── documents/
│   ├── models.py          # Folder, Document, ACL, AuditLog
│   ├── views.py           # Views + preview logic
│   ├── forms.py           # Upload/folder forms
│   ├── permissions.py     # ACL enforcement
│   └── utils.py           # File handling
├── templates/
│   ├── base.html
│   └── documents/
│       ├── folder_list.html
│       ├── folder_tree.html
│       ├── folder_tree_recursive.html
│       ├── preview.html   # Multi-format preview
│       ├── upload.html
│       └── detail.html
└── static/css/style.css
```

## API Reference

**Models**:
- Tenant, TenantUser, Role, Group
- Folder, FolderACL (hierarchical structure)
- StoredFile, Document, ACL
- AuditLog

**Key Views**:
- `folder_list`: Tree view + folder contents
- `folder_create`, `folder_delete`
- `document_upload`, `document_detail`
- `document_preview`, `document_preview_content`: Multi-format preview
- `document_download`, `document_delete`

## Security

### File Upload
- Whitelist validation (40+ types)
- Size limits (50MB default)
- Storage outside web root
- Checksum verification

### Permissions
- Operation-level checks
- Folder inheritance
- Owner full access
- Download requires explicit permission

### Database
- PostgreSQL: Schema isolation
- SQL injection prevention
- CSRF protection
- Audit logging

### Production Checklist
- [ ] Change SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Use PostgreSQL
- [ ] Enable HTTPS
- [ ] Configure backups
- [ ] Add virus scanning
- [ ] Implement rate limiting

## Testing

```bash
python manage.py test
python manage.py test documents.tests.FolderTestCase
```

Coverage: Multi-tenancy, folders, ACLs, deduplication, audit logs

## Troubleshooting

**Subdomain Issues**:
Edit hosts file:
```
127.0.0.1 companya.localhost
127.0.0.1 companyb.localhost
```

Or enable development mode in `tenants/middleware.py`

**Preview Not Working**:
- Check file permissions
- Verify MIME type detection
- Review browser console

**Permission Denied**:
- Verify TenantUser record
- Check Role assignment
- Review folder/document ACLs

## Database Migration (SQLite → PostgreSQL)

```bash
# Backup
python manage.py dumpdata > backup.json

# Update .env to PostgreSQL
# Create database
createdb docmanager

# Migrate
python manage.py migrate

# Recreate tenants
python manage.py create_tenant "Company A" --domain=companya

# Load data
python manage.py loaddata backup.json
```
---

**Key Capabilities**:
- ✅ Multi-tenant (PostgreSQL/SQLite)
- ✅ Hierarchical folders with tree view
- ✅ 40+ file type preview
- ✅ Granular permissions (folders + documents)
- ✅ File deduplication (SHA256)
- ✅ Audit logging
- ✅ Production-ready security

## 🪪 License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this software for personal, educational, or commercial purposes, provided that the original copyright 
and permission notice are included in all copies or substantial portions of the Software.

See the [LICENSE](LICENSE) file for the full license text.

## Support

For issues and questions:
- Check the troubleshooting section
- Review test cases for usage examples
- Consult [Django](https://www.djangoproject.com/) documentation for framework-specific questions

---




