"""
Management command to create a new tenant.
For PostgreSQL: creates schema and runs migrations.
For SQLite: creates tenant record only.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Create a new tenant (with schema for PostgreSQL)'
    
    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Tenant name')
        parser.add_argument('--domain', type=str, help='Domain/subdomain for tenant')
    
    def handle(self, *args, **options):
        name = options['name']
        domain = options.get('domain') or name.lower().replace(' ', '_')
        schema_name = domain
        
        is_postgres = 'postgresql' in settings.DATABASES['default']['ENGINE']
        
        # Check if tenant exists
        if Tenant.objects.filter(name=name).exists():
            self.stdout.write(self.style.ERROR(f'Tenant "{name}" already exists'))
            return
        
        # Create tenant
        tenant = Tenant.objects.create(
            name=name,
            schema_name=schema_name,
            domain=domain
        )
        
        self.stdout.write(self.style.SUCCESS(f'Created tenant: {name}'))
        
        if is_postgres:
            # Create PostgreSQL schema
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
                self.stdout.write(self.style.SUCCESS(f'Created schema: {schema_name}'))
                
                # Set search path and create tables
                cursor.execute(f'SET search_path TO {schema_name}, public')
            
            # Run migrations in the schema
            from django.core.management import call_command
            call_command('migrate', '--run-syncdb', '--database=default')
            
            self.stdout.write(self.style.SUCCESS(f'Ran migrations for schema: {schema_name}'))
        else:
            self.stdout.write(self.style.SUCCESS('SQLite mode: tenant record created'))
        
        self.stdout.write(self.style.SUCCESS(f'\nTenant created successfully!'))
        self.stdout.write(f'Access at: http://{domain}.localhost:8000')