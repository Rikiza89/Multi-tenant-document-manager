# Multi-Tenant Document Management System

A Django-based document management system with multi-tenant architecture, supporting both SQLite (development) and PostgreSQL (production) databases.

## Features

- **Multi-Tenant Architecture**: Shared database with tenant isolation
  - PostgreSQL: Schema-based separation
  - SQLite: Tenant ID-based filtering
- **Document Management**: Upload, search, view metadata, and download documents
- **Access Control**: Multi-level permissions (roles, groups, per-file ACLs)
- **File Deduplication**: SHA256 checksum-based duplicate detection
- **Audit Logging**: Complete audit trail of all document operations
- **Responsive UI**: Clean, minimal interface with no heavy frontend frameworks
- **Security**: File validation, permission enforcement, CSRF protection

## Requirements

- Python 3.11+
- Django 4.2+
- PostgreSQL (for production) or SQLite (for development)


**Project Structure**:
```
docmanager/
├── docmanager/          # Project settings
│   ├── settings.py      # Configuration
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI application
├── tenants/             # Multi-tenancy app
│   ├── models.py        # Tenant models
│   ├── middleware.py    # Tenant resolution
│   └── management/      # Tenant commands
├── documents/           # Document management
│   ├── models.py        # Document models
│   ├── views.py         # Views
│   ├── forms.py         # Forms
│   ├── permissions.py   # ACL logic
│   └── utils.py         # Utilities
├── templates/           # HTML templates
├── static/              # CSS/JS files
├── media/               # Uploaded files
└── requirements.txt     # Dependencies
```

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd docmanager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

For **SQLite (Development)**:
```env
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.localhost
TENANT_UNIQUENESS=global
```

For **PostgreSQL (Production)**:
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
TENANT_UNIQUENESS=global
```

### 3. Run Migrations

```bash
# Create database tables
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 4. Create Tenants

```bash
# Create first tenant
python manage.py create_tenant "Company A" --domain=companya

# Create second tenant
python manage.py create_tenant "Company B" --domain=companyb
```

For PostgreSQL, this will:
- Create a dedicated schema for each tenant
- Run migrations within the schema

For SQLite, this will:
- Create a tenant record
- Enable tenant-based filtering

### 5. Create Users and Assign Roles

```bash
# Access Django admin
python manage.py runserver
# Navigate to http://localhost:8000/admin/

# Create users and assign them to tenants via TenantUser
# Assign roles via the Role model
```

## Running the Application

### Development (SQLite)

```bash
python manage.py runserver
```

Access tenants via:
- http://companya.localhost:8000
- http://companyb.localhost:8000

### Production (PostgreSQL)

```bash
# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn docmanager.wsgi:application --bind 0.0.0.0:8000
```

Configure your web server (Nginx/Apache) to handle tenant routing via subdomains.

## Usage Guide

### Document Upload

1. Login to your tenant domain
2. Click "Upload Document"
3. Fill in document details:
   - Title (required)
   - Description (optional)
   - Tags (comma-separated, optional)
   - File (required)
4. Click "Upload"

**File Validation**:
- Maximum size: 50MB (configurable)
- Allowed types: pdf, doc, docx, txt, xls, xlsx, png, jpg, jpeg

### File Deduplication

The system automatically detects duplicate files using SHA256 checksums:

- **Global mode** (`TENANT_UNIQUENESS=global`): Prevents duplicates across all tenants
- **Per-tenant mode** (`TENANT_UNIQUENESS=per_tenant`): Allows same file in different tenants

### Access Control

**Three-level permission system**:

1. **Roles** (tenant-wide):
   - Admin: Full access to all documents
   - Editor: Read, download, and edit documents
   - Viewer: Read-only access

2. **Groups**: Organize users and assign permissions collectively

3. **ACLs** (per-document):
   - Read: View metadata
   - Download: Download file
   - Edit: Modify document
   - Delete: Remove document

### Searching Documents

Use the search bar to find documents by:
- Title
- Description
- Original filename
- Tags

## Multi-Tenancy Implementation

### PostgreSQL Mode

```python
# Tenant middleware sets schema per request
SET search_path TO tenant1, public;
```

Each tenant gets an isolated schema with complete data separation.

### SQLite Mode

```python
# All models include tenant foreign key
# Filtering happens at ORM level
documents = Document.objects.filter(tenant=current_tenant)
```

Tenant isolation through application-level filtering.

## API Structure

### Models

- **Tenant**: Represents a tenant organization
- **TenantUser**: Links users to tenants
- **Role**: User roles within tenants
- **Group**: User groups for collective permissions
- **StoredFile**: Physical file with checksum
- **Document**: Document metadata linked to tenant
- **ACL**: Access control entries
- **AuditLog**: Activity audit trail

### Views

- `document_list`: List all accessible documents
- `document_upload`: Upload new document
- `document_detail`: View document details and ACLs
- `document_download`: Download file (permission-checked)
- `document_delete`: Delete document (permission-checked)

## Security Considerations

### File Upload Security

- File type validation (whitelist-based)
- File size limits
- Virus scanning (recommended to add)
- Secure file storage outside web root

### Permission Enforcement

- All downloads require explicit permission
- Decorator-based permission checks
- Owner always has full access
- Role-based access control

### Database Security

- PostgreSQL: Schema isolation prevents cross-tenant queries
- SQLite: Application-level filtering (less secure, dev only)
- Prepared statements prevent SQL injection
- CSRF protection enabled

### Production Checklist

- [ ] Change SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS
- [ ] Configure file upload limits
- [ ] Set up backup strategy
- [ ] Enable access logging
- [ ] Implement rate limiting
- [ ] Add virus scanning
- [ ] Configure email notifications

## Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run specific test class
python manage.py test documents.tests.ACLTestCase

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

**Test Coverage**:
- Multi-tenancy isolation
- File deduplication (global and per-tenant)
- ACL permissions
- Role-based access
- Audit logging

## Database Migration Guide

### SQLite to PostgreSQL Migration

1. **Backup SQLite data**:
```bash
python manage.py dumpdata > backup.json
```

2. **Update .env for PostgreSQL**:
```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=docmanager
DATABASE_USER=postgres
DATABASE_PASSWORD=yourpassword
```

3. **Create PostgreSQL database**:
```sql
CREATE DATABASE docmanager;
```

4. **Run migrations**:
```bash
python manage.py migrate
```

5. **Create schemas for existing tenants**:
```bash
# For each tenant in backup
python manage.py create_tenant "Tenant Name" --domain=tenantdomain
```

6. **Load data** (with caution):
```bash
python manage.py loaddata backup.json
```

Note: Files must be manually copied to new MEDIA_ROOT location.

## Troubleshooting

### Tenant Not Found

- Ensure tenant domain matches exactly
- Check ALLOWED_HOSTS includes `.localhost` for development
- Verify tenant is active (`is_active=True`)

### Permission Denied

- Check user has TenantUser record for current tenant
- Verify Role assignment
- Check document ACLs

### File Upload Fails

- Verify MEDIA_ROOT directory exists and is writable
- Check file size and type restrictions
- Review application logs

### PostgreSQL Schema Issues

```bash
# List all schemas
psql -d docmanager -c "\dn"

# Check search_path
SELECT current_schemas(true);

# Manually set schema
SET search_path TO tenant1, public;
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 🪪 License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this software for personal, educational, or commercial purposes, provided that the original copyright 
and permission notice are included in all copies or substantial portions of the Software.

See the [LICENSE](LICENSE) file for the full license text.

## Support

For issues and questions:
- Check the troubleshooting section
- Review test cases for usage examples
- Consult Django documentation for framework-specific questions

---
