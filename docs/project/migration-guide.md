# Migration Guide

## Django GraphQL Auto-Generation System - Migration Guide

This guide provides detailed instructions for migrating between different versions of the Django GraphQL Auto-Generation System, including breaking changes, deprecated features, and upgrade procedures.

## Table of Contents

- [General Migration Process](#general-migration-process)
- [Version-Specific Migrations](#version-specific-migrations)
- [Breaking Changes](#breaking-changes)
- [Deprecated Features](#deprecated-features)
- [Database Migrations](#database-migrations)
- [Configuration Changes](#configuration-changes)
- [Code Updates](#code-updates)
- [Testing After Migration](#testing-after-migration)
- [Rollback Procedures](#rollback-procedures)
- [Migration Tools](#migration-tools)

## General Migration Process

### Pre-Migration Checklist

Before starting any migration, ensure you have:

- [ ] **Full backup** of your database and application code
- [ ] **Test environment** that mirrors production
- [ ] **Downtime window** scheduled (if required)
- [ ] **Rollback plan** prepared and tested
- [ ] **Team notification** about the migration
- [ ] **Dependencies updated** to compatible versions
- [ ] **Documentation reviewed** for the target version

### Migration Steps

1. **Preparation Phase**
   ```bash
   # Create backup
   python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
   
   # Export current schema
   python manage.py graphql_schema --out current_schema.graphql
   
   # Document current configuration
   python manage.py diffsettings > current_settings.txt
   ```

2. **Testing Phase**
   ```bash
   # Test in development environment
   git checkout migration-branch
   pip install -r requirements.txt
   python manage.py migrate --dry-run
   python manage.py test
   ```

3. **Migration Phase**
   ```bash
   # Apply migrations
   python manage.py migrate
   
   # Update static files
   python manage.py collectstatic --noinput
   
   # Clear cache
   python manage.py clear_cache
   ```

4. **Verification Phase**
   ```bash
   # Verify schema
   python manage.py graphql_schema --out new_schema.graphql
   diff current_schema.graphql new_schema.graphql
   
   # Run tests
   python manage.py test
   
   # Check health
   curl -f http://localhost:8000/health/
   ```

## Version-Specific Migrations

### Migrating from v1.0 to v2.0

#### Overview
Version 2.0 introduces significant changes to the schema generation system, enhanced security features, and improved performance optimizations.

#### Breaking Changes

1. **Schema Generation API Changes**
   ```python
   # v1.0 (deprecated)
   from graphql_auto_gen import AutoSchema
   schema = AutoSchema(models=[User, Product])
   
   # v2.0 (new)
   from graphql_auto_gen import SchemaBuilder
   from graphql_auto_gen.config import SchemaConfig
   
   config = SchemaConfig(
       models=[User, Product],
       enable_mutations=True,
       enable_subscriptions=False
   )
   schema = SchemaBuilder(config).build()
   ```

2. **Configuration Structure Changes**
   ```python
   # v1.0 settings.py
   GRAPHQL_AUTO_GEN = {
       'MODELS': ['app.models.User', 'app.models.Product'],
       'ENABLE_MUTATIONS': True,
   }
   
   # v2.0 settings.py
   GRAPHQL_AUTO_GEN = {
       'SCHEMA_CONFIG': {
           'models': ['app.models.User', 'app.models.Product'],
           'mutations': {
               'enabled': True,
               'bulk_operations': True,
               'soft_delete': True,
           },
           'queries': {
               'pagination': 'relay',
               'filtering': 'advanced',
               'ordering': True,
           },
           'security': {
               'authentication_required': True,
               'permission_classes': ['IsAuthenticated'],
               'rate_limiting': True,
           }
       }
   }
   ```

3. **Field Resolver Changes**
   ```python
   # v1.0 custom resolvers
   class UserType(DjangoObjectType):
       full_name = graphene.String()
       
       def resolve_full_name(self, info):
           return f"{self.first_name} {self.last_name}"
   
   # v2.0 custom resolvers (enhanced)
   from graphql_auto_gen.resolvers import BaseResolver
   
   class UserResolver(BaseResolver):
       model = User
       
       @cached_field
       def resolve_full_name(self, info):
           return f"{self.first_name} {self.last_name}"
       
       @permission_required('users.view_user')
       def resolve_email(self, info):
           return self.email
   ```

#### Migration Steps

1. **Update Dependencies**
   ```bash
   # Update requirements.txt
   django-graphql-auto-gen>=2.0.0,<3.0.0
   
   # Install new version
   pip install -r requirements.txt
   ```

2. **Update Configuration**
   ```python
   # Create migration script: migrate_config_v2.py
   import os
   import django
   from django.conf import settings
   
   def migrate_config():
       """Migrate v1.0 config to v2.0 format."""
       old_config = getattr(settings, 'GRAPHQL_AUTO_GEN', {})
       
       new_config = {
           'SCHEMA_CONFIG': {
               'models': old_config.get('MODELS', []),
               'mutations': {
                   'enabled': old_config.get('ENABLE_MUTATIONS', True),
                   'bulk_operations': True,
                   'soft_delete': False,
               },
               'queries': {
                   'pagination': 'relay',
                   'filtering': 'basic',
                   'ordering': True,
               },
               'security': {
                   'authentication_required': False,
                   'permission_classes': [],
                   'rate_limiting': False,
               }
           }
       }
       
       print("New configuration:")
       print(f"GRAPHQL_AUTO_GEN = {new_config}")
   
   if __name__ == '__main__':
       migrate_config()
   ```

3. **Update Code**
   ```python
   # Create code migration script: migrate_code_v2.py
   import ast
   import os
   
   class CodeMigrator(ast.NodeTransformer):
       """Migrate v1.0 code to v2.0."""
       
       def visit_ImportFrom(self, node):
           # Update imports
           if node.module == 'graphql_auto_gen':
               if any(alias.name == 'AutoSchema' for alias in node.names):
                   # Replace AutoSchema import
                   return ast.ImportFrom(
                       module='graphql_auto_gen',
                       names=[
                           ast.alias(name='SchemaBuilder', asname=None),
                           ast.alias(name='SchemaConfig', asname=None)
                       ],
                       level=0
                   )
           return node
       
       def visit_Call(self, node):
           # Update AutoSchema calls
           if (isinstance(node.func, ast.Name) and 
               node.func.id == 'AutoSchema'):
               # Convert to SchemaBuilder
               return ast.Call(
                   func=ast.Attribute(
                       value=ast.Call(
                           func=ast.Name(id='SchemaBuilder', ctx=ast.Load()),
                           args=[ast.Call(
                               func=ast.Name(id='SchemaConfig', ctx=ast.Load()),
                               args=[],
                               keywords=node.keywords
                           )],
                           keywords=[]
                       ),
                       attr='build',
                       ctx=ast.Load()
                   ),
                   args=[],
                   keywords=[]
               )
           return node
   
   def migrate_file(filepath):
       """Migrate a single Python file."""
       with open(filepath, 'r') as f:
           source = f.read()
       
       tree = ast.parse(source)
       migrator = CodeMigrator()
       new_tree = migrator.visit(tree)
       
       new_source = ast.unparse(new_tree)
       
       # Backup original
       backup_path = f"{filepath}.v1_backup"
       os.rename(filepath, backup_path)
       
       # Write migrated code
       with open(filepath, 'w') as f:
           f.write(new_source)
       
       print(f"Migrated {filepath} (backup: {backup_path})")
   
   # Usage
   migrate_file('your_app/schema.py')
   ```

4. **Database Migration**
   ```python
   # Create Django migration: 0002_migrate_to_v2.py
   from django.db import migrations
   
   def migrate_graphql_metadata(apps, schema_editor):
       """Migrate GraphQL metadata to v2.0 format."""
       # Update any stored GraphQL metadata
       pass
   
   def reverse_migrate_graphql_metadata(apps, schema_editor):
       """Reverse migration for rollback."""
       pass
   
   class Migration(migrations.Migration):
       dependencies = [
           ('your_app', '0001_initial'),
       ]
       
       operations = [
           migrations.RunPython(
               migrate_graphql_metadata,
               reverse_migrate_graphql_metadata
           ),
       ]
   ```

### Migrating from v2.0 to v2.1

#### Overview
Version 2.1 introduces enhanced filtering capabilities, improved performance, and additional security features.

#### Changes

1. **Enhanced Filtering**
   ```python
   # v2.0 filtering
   users(filter: {name: "John"})
   
   # v2.1 filtering (backward compatible)
   users(filter: {
       name: {contains: "John", icontains: "john"}
       createdAt: {gte: "2023-01-01", lte: "2023-12-31"}
       isActive: true
   })
   ```

2. **Performance Improvements**
   ```python
   # v2.1 adds automatic query optimization
   # No code changes required, but benefits from:
   # - Automatic select_related/prefetch_related
   # - Query complexity analysis
   # - Enhanced caching
   ```

#### Migration Steps

1. **Update Dependencies**
   ```bash
   pip install django-graphql-auto-gen>=2.1.0,<2.2.0
   ```

2. **Optional Configuration Updates**
   ```python
   # settings.py - Optional enhancements
   GRAPHQL_AUTO_GEN = {
       'SCHEMA_CONFIG': {
           # ... existing config ...
           'queries': {
               'pagination': 'relay',
               'filtering': 'advanced',  # Enhanced filtering
               'ordering': True,
               'query_optimization': True,  # New in v2.1
           },
           'performance': {  # New section in v2.1
               'enable_query_analysis': True,
               'max_query_complexity': 1000,
               'enable_automatic_optimization': True,
           }
       }
   }
   ```

### Migrating from v2.1 to v3.0

#### Overview
Version 3.0 introduces async support, GraphQL subscriptions, and a redesigned plugin system.

#### Breaking Changes

1. **Async Support**
   ```python
   # v2.1 synchronous resolvers
   def resolve_users(self, info):
       return User.objects.all()
   
   # v3.0 async resolvers (optional but recommended)
   async def resolve_users(self, info):
       return await User.objects.aall()
   ```

2. **Plugin System**
   ```python
   # v2.1 custom extensions
   class CustomExtension:
       def process_schema(self, schema):
           # Custom processing
           return schema
   
   # v3.0 plugin system
   from graphql_auto_gen.plugins import BasePlugin
   
   class CustomPlugin(BasePlugin):
       name = "custom_plugin"
       version = "1.0.0"
       
       async def process_schema(self, schema, context):
           # Async processing
           return schema
       
       def get_config_schema(self):
           return {
               'type': 'object',
               'properties': {
                   'enabled': {'type': 'boolean'},
                   'options': {'type': 'object'}
               }
           }
   ```

#### Migration Steps

1. **Update Dependencies**
   ```bash
   pip install django-graphql-auto-gen>=3.0.0,<4.0.0
   ```

2. **Enable Async Support (Optional)**
   ```python
   # settings.py
   GRAPHQL_AUTO_GEN = {
       'SCHEMA_CONFIG': {
           # ... existing config ...
           'async_support': True,  # Enable async resolvers
           'subscriptions': {      # New in v3.0
               'enabled': True,
               'transport': 'websocket',
               'authentication_required': True,
           }
       }
   }
   ```

3. **Migrate Custom Extensions to Plugins**
   ```python
   # Create plugin migration script
   def migrate_extensions_to_plugins():
       """Convert v2.1 extensions to v3.0 plugins."""
       # Implementation depends on your custom extensions
       pass
   ```

## Breaking Changes

### Summary of Breaking Changes by Version

#### v2.0.0
- **Schema Generation API**: Complete rewrite of schema generation
- **Configuration Format**: New nested configuration structure
- **Import Paths**: Changed import paths for main classes
- **Resolver Interface**: Enhanced resolver base classes

#### v3.0.0
- **Plugin System**: Replaced extension system with plugins
- **Async Support**: New async resolver interface
- **Subscription Support**: New subscription system
- **Python Version**: Minimum Python 3.9 required

### Handling Breaking Changes

1. **Automated Migration Tools**
   ```bash
   # Use built-in migration tool
   python manage.py migrate_graphql_schema --from-version=1.0 --to-version=2.0
   
   # Check for breaking changes
   python manage.py check_graphql_compatibility --target-version=2.0
   ```

2. **Manual Migration Checklist**
   ```python
   # Create checklist for manual migration
   MIGRATION_CHECKLIST = [
       "Update import statements",
       "Migrate configuration format",
       "Update custom resolvers",
       "Test schema generation",
       "Update client queries if needed",
       "Verify permissions and security",
       "Test performance impact",
       "Update documentation",
   ]
   ```

## Deprecated Features

### Deprecation Timeline

#### v2.0 Deprecations (Removed in v3.0)
- `AutoSchema` class → Use `SchemaBuilder`
- `GRAPHQL_AUTO_GEN.MODELS` → Use `SCHEMA_CONFIG.models`
- `simple_resolver` decorator → Use `@resolver` decorator

#### v2.1 Deprecations (Removed in v3.1)
- `basic` filtering mode → Use `advanced` filtering
- `legacy_pagination` → Use `relay` pagination
- `SimpleExtension` → Use plugin system

#### v3.0 Deprecations (Will be removed in v4.0)
- Synchronous-only resolvers → Migrate to async
- `old_plugin_interface` → Use new plugin base class

### Handling Deprecated Features

```python
# Create deprecation warning handler
import warnings
from graphql_auto_gen.deprecation import GraphQLDeprecationWarning

def handle_deprecations():
    """Handle deprecated feature usage."""
    # Show deprecation warnings in development
    if settings.DEBUG:
        warnings.filterwarnings('default', category=GraphQLDeprecationWarning)
    else:
        warnings.filterwarnings('ignore', category=GraphQLDeprecationWarning)

# Add to Django settings
handle_deprecations()
```

## Database Migrations

### Schema Changes

```python
# Example migration for schema metadata changes
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('graphql_auto_gen', '0001_initial'),
    ]
    
    operations = [
        # Add new fields for v2.0 features
        migrations.AddField(
            model_name='schemametadata',
            name='version',
            field=models.CharField(max_length=20, default='2.0.0'),
        ),
        migrations.AddField(
            model_name='schemametadata',
            name='config_hash',
            field=models.CharField(max_length=64, null=True),
        ),
        
        # Migrate existing data
        migrations.RunPython(
            migrate_schema_metadata,
            reverse_migrate_schema_metadata
        ),
    ]

def migrate_schema_metadata(apps, schema_editor):
    """Migrate existing schema metadata to new format."""
    SchemaMetadata = apps.get_model('graphql_auto_gen', 'SchemaMetadata')
    
    for metadata in SchemaMetadata.objects.all():
        # Update metadata format
        metadata.version = '2.0.0'
        metadata.config_hash = calculate_config_hash(metadata.config)
        metadata.save()

def reverse_migrate_schema_metadata(apps, schema_editor):
    """Reverse migration for rollback."""
    SchemaMetadata = apps.get_model('graphql_auto_gen', 'SchemaMetadata')
    
    for metadata in SchemaMetadata.objects.all():
        # Revert to old format
        metadata.version = '1.0.0'
        metadata.config_hash = None
        metadata.save()
```

### Data Migration Scripts

```python
# data_migration.py
import json
from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    """Migrate GraphQL-related data between versions."""
    
    help = 'Migrate GraphQL data between versions'
    
    def add_arguments(self, parser):
        parser.add_argument('--from-version', required=True)
        parser.add_argument('--to-version', required=True)
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        from_version = options['from_version']
        to_version = options['to_version']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Migrating from {from_version} to {to_version}")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
        
        # Perform version-specific migrations
        if from_version == '1.0' and to_version == '2.0':
            self.migrate_1_0_to_2_0(dry_run)
        elif from_version == '2.0' and to_version == '2.1':
            self.migrate_2_0_to_2_1(dry_run)
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Migration from {from_version} to {to_version} not supported"
                )
            )
    
    def migrate_1_0_to_2_0(self, dry_run):
        """Migrate data from v1.0 to v2.0."""
        # Implementation specific to your data model
        pass
    
    def migrate_2_0_to_2_1(self, dry_run):
        """Migrate data from v2.0 to v2.1."""
        # Implementation specific to your data model
        pass
```

## Configuration Changes

### Configuration Migration Tool

```python
# config_migrator.py
import json
import yaml
from pathlib import Path

class ConfigMigrator:
    """Migrate configuration between versions."""
    
    def __init__(self, from_version, to_version):
        self.from_version = from_version
        self.to_version = to_version
    
    def migrate_settings(self, settings_path):
        """Migrate Django settings file."""
        with open(settings_path, 'r') as f:
            content = f.read()
        
        # Apply version-specific transformations
        if self.from_version == '1.0' and self.to_version == '2.0':
            content = self._migrate_1_0_to_2_0_settings(content)
        
        # Backup original
        backup_path = f"{settings_path}.backup"
        Path(settings_path).rename(backup_path)
        
        # Write migrated settings
        with open(settings_path, 'w') as f:
            f.write(content)
        
        print(f"Migrated {settings_path} (backup: {backup_path})")
    
    def _migrate_1_0_to_2_0_settings(self, content):
        """Migrate v1.0 settings to v2.0 format."""
        # Use regex or AST parsing to transform settings
        import re
        
        # Replace old configuration format
        old_pattern = r'GRAPHQL_AUTO_GEN\s*=\s*{([^}]+)}'
        
        def replace_config(match):
            old_config = match.group(1)
            # Parse and transform configuration
            # This is a simplified example
            new_config = """
    'SCHEMA_CONFIG': {
        'models': [],  # Add your models here
        'mutations': {'enabled': True},
        'queries': {'pagination': 'relay'},
        'security': {'authentication_required': False}
    }"""
            return f'GRAPHQL_AUTO_GEN = {{{new_config}}}'
        
        return re.sub(old_pattern, replace_config, content, flags=re.DOTALL)

# Usage
migrator = ConfigMigrator('1.0', '2.0')
migrator.migrate_settings('settings/production.py')
```

## Code Updates

### Automated Code Migration

```python
# code_migrator.py
import ast
import astor
from pathlib import Path

class GraphQLCodeMigrator(ast.NodeTransformer):
    """Migrate GraphQL-related code between versions."""
    
    def __init__(self, from_version, to_version):
        self.from_version = from_version
        self.to_version = to_version
        self.changes = []
    
    def visit_ImportFrom(self, node):
        """Migrate import statements."""
        if node.module and 'graphql_auto_gen' in node.module:
            if self.from_version == '1.0' and self.to_version == '2.0':
                return self._migrate_imports_1_0_to_2_0(node)
        return node
    
    def visit_Call(self, node):
        """Migrate function calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id == 'AutoSchema' and self.to_version == '2.0':
                return self._migrate_auto_schema_call(node)
        return node
    
    def _migrate_imports_1_0_to_2_0(self, node):
        """Migrate v1.0 imports to v2.0."""
        new_names = []
        for alias in node.names:
            if alias.name == 'AutoSchema':
                new_names.extend([
                    ast.alias(name='SchemaBuilder', asname=None),
                    ast.alias(name='SchemaConfig', asname=None)
                ])
                self.changes.append("Replaced AutoSchema import with SchemaBuilder and SchemaConfig")
            else:
                new_names.append(alias)
        
        node.names = new_names
        return node
    
    def _migrate_auto_schema_call(self, node):
        """Migrate AutoSchema() calls to SchemaBuilder()."""
        # Create SchemaConfig call
        config_call = ast.Call(
            func=ast.Name(id='SchemaConfig', ctx=ast.Load()),
            args=[],
            keywords=node.keywords
        )
        
        # Create SchemaBuilder call
        builder_call = ast.Call(
            func=ast.Name(id='SchemaBuilder', ctx=ast.Load()),
            args=[config_call],
            keywords=[]
        )
        
        # Create build() method call
        build_call = ast.Call(
            func=ast.Attribute(
                value=builder_call,
                attr='build',
                ctx=ast.Load()
            ),
            args=[],
            keywords=[]
        )
        
        self.changes.append("Migrated AutoSchema() to SchemaBuilder().build()")
        return build_call

def migrate_python_file(file_path, from_version, to_version):
    """Migrate a Python file between versions."""
    with open(file_path, 'r') as f:
        source = f.read()
    
    try:
        tree = ast.parse(source)
        migrator = GraphQLCodeMigrator(from_version, to_version)
        new_tree = migrator.visit(tree)
        
        if migrator.changes:
            # Backup original
            backup_path = f"{file_path}.backup"
            Path(file_path).rename(backup_path)
            
            # Write migrated code
            new_source = astor.to_source(new_tree)
            with open(file_path, 'w') as f:
                f.write(new_source)
            
            print(f"Migrated {file_path}:")
            for change in migrator.changes:
                print(f"  - {change}")
            print(f"  Backup: {backup_path}")
        else:
            print(f"No changes needed for {file_path}")
    
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        print(f"Error migrating {file_path}: {e}")

# Usage
migrate_python_file('your_app/schema.py', '1.0', '2.0')
```

## Testing After Migration

### Migration Test Suite

```python
# test_migration.py
import unittest
from django.test import TestCase
from django.core.management import call_command
from graphql import build_schema
from graphql.execution import execute

class MigrationTestCase(TestCase):
    """Test suite for migration verification."""
    
    def setUp(self):
        """Set up test data."""
        # Create test data that should work before and after migration
        pass
    
    def test_schema_compatibility(self):
        """Test that schema is compatible after migration."""
        # Generate schema
        from your_app.schema import schema
        
        # Test basic query
        query = """
        query {
            users {
                id
                username
                email
            }
        }
        """
        
        result = execute(schema, query)
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
    
    def test_mutation_compatibility(self):
        """Test that mutations work after migration."""
        mutation = """
        mutation {
            createUser(input: {
                username: "testuser"
                email: "test@example.com"
                password: "testpass123"
            }) {
                user {
                    id
                    username
                }
                success
                errors {
                    field
                    message
                }
            }
        }
        """
        
        from your_app.schema import schema
        result = execute(schema, mutation)
        self.assertIsNone(result.errors)
    
    def test_filtering_compatibility(self):
        """Test that filtering works after migration."""
        query = """
        query {
            users(filter: {username: "testuser"}) {
                id
                username
            }
        }
        """
        
        from your_app.schema import schema
        result = execute(schema, query)
        self.assertIsNone(result.errors)
    
    def test_pagination_compatibility(self):
        """Test that pagination works after migration."""
        query = """
        query {
            users(first: 10) {
                edges {
                    node {
                        id
                        username
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        from your_app.schema import schema
        result = execute(schema, query)
        self.assertIsNone(result.errors)
    
    def test_performance_regression(self):
        """Test for performance regressions after migration."""
        import time
        
        query = """
        query {
            users {
                id
                username
                profile {
                    firstName
                    lastName
                }
            }
        }
        """
        
        from your_app.schema import schema
        
        start_time = time.time()
        result = execute(schema, query)
        duration = time.time() - start_time
        
        self.assertIsNone(result.errors)
        self.assertLess(duration, 1.0)  # Should complete within 1 second

class MigrationIntegrationTest(TestCase):
    """Integration tests for migration."""
    
    def test_full_migration_workflow(self):
        """Test complete migration workflow."""
        # This would test the entire migration process
        # in a controlled environment
        pass
    
    def test_rollback_capability(self):
        """Test that migration can be rolled back."""
        # Test rollback procedures
        pass

# Run migration tests
if __name__ == '__main__':
    unittest.main()
```

### Performance Comparison

```python
# performance_comparison.py
import time
import statistics
from django.test import TestCase
from graphql.execution import execute

class PerformanceComparisonTest(TestCase):
    """Compare performance before and after migration."""
    
    def setUp(self):
        """Set up test data."""
        # Create substantial test data
        pass
    
    def benchmark_query(self, query, iterations=10):
        """Benchmark a GraphQL query."""
        from your_app.schema import schema
        
        times = []
        for _ in range(iterations):
            start_time = time.time()
            result = execute(schema, query)
            duration = time.time() - start_time
            
            self.assertIsNone(result.errors)
            times.append(duration)
        
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times)
        }
    
    def test_simple_query_performance(self):
        """Benchmark simple queries."""
        query = """
        query {
            users {
                id
                username
            }
        }
        """
        
        stats = self.benchmark_query(query)
        print(f"Simple query performance: {stats}")
        
        # Assert performance is acceptable
        self.assertLess(stats['mean'], 0.5)  # Average under 500ms
    
    def test_complex_query_performance(self):
        """Benchmark complex queries with relationships."""
        query = """
        query {
            users {
                id
                username
                profile {
                    firstName
                    lastName
                }
                orders {
                    id
                    total
                    items {
                        id
                        product {
                            name
                            price
                        }
                    }
                }
            }
        }
        """
        
        stats = self.benchmark_query(query)
        print(f"Complex query performance: {stats}")
        
        # Assert performance is acceptable
        self.assertLess(stats['mean'], 2.0)  # Average under 2 seconds
```

## Rollback Procedures

### Automated Rollback

```bash
#!/bin/bash
# rollback.sh

set -e

VERSION_FROM=$1
VERSION_TO=$2

if [ -z "$VERSION_FROM" ] || [ -z "$VERSION_TO" ]; then
    echo "Usage: $0 <from_version> <to_version>"
    echo "Example: $0 2.0 1.0"
    exit 1
fi

echo "Rolling back from version $VERSION_FROM to $VERSION_TO"

# Stop services
echo "Stopping services..."
docker-compose stop

# Restore database backup
echo "Restoring database backup..."
BACKUP_FILE="backup_before_${VERSION_FROM}.sql"
if [ -f "$BACKUP_FILE" ]; then
    psql -h localhost -U graphql_user -d graphql_db < "$BACKUP_FILE"
else
    echo "Warning: No database backup found for version $VERSION_FROM"
fi

# Restore code backup
echo "Restoring code backup..."
if [ -d "backup_before_${VERSION_FROM}" ]; then
    rm -rf current_code
    mv backup_before_${VERSION_FROM} current_code
else
    echo "Warning: No code backup found for version $VERSION_FROM"
fi

# Install previous version
echo "Installing version $VERSION_TO..."
pip install "django-graphql-auto-gen==$VERSION_TO"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --fake-initial

# Restart services
echo "Starting services..."
docker-compose start

echo "Rollback completed successfully"
```

### Manual Rollback Checklist

```python
# rollback_checklist.py
ROLLBACK_CHECKLIST = {
    "pre_rollback": [
        "Verify rollback necessity",
        "Identify target version",
        "Locate backups (database, code, config)",
        "Notify team about rollback",
        "Schedule maintenance window",
    ],
    "rollback_execution": [
        "Stop application services",
        "Restore database from backup",
        "Restore code from backup",
        "Install previous package version",
        "Restore configuration files",
        "Run database migrations (if needed)",
        "Clear caches",
        "Restart services",
    ],
    "post_rollback": [
        "Verify application functionality",
        "Test critical user flows",
        "Monitor error logs",
        "Check performance metrics",
        "Notify team of completion",
        "Document rollback reasons",
        "Plan forward migration strategy",
    ]
}

def print_rollback_checklist():
    """Print rollback checklist."""
    for phase, items in ROLLBACK_CHECKLIST.items():
        print(f"\n{phase.upper().replace('_', ' ')}:")
        for item in items:
            print(f"  [ ] {item}")

if __name__ == '__main__':
    print_rollback_checklist()
```

## Migration Tools

### Migration CLI Tool

```python
# management/commands/migrate_graphql.py
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import subprocess
import json
import os

class Command(BaseCommand):
    """Django management command for GraphQL migrations."""
    
    help = 'Migrate GraphQL Auto-Generation System between versions'
    
    def add_arguments(self, parser):
        parser.add_argument('--from-version', required=True, help='Source version')
        parser.add_argument('--to-version', required=True, help='Target version')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
        parser.add_argument('--backup', action='store_true', help='Create backup before migration')
        parser.add_argument('--force', action='store_true', help='Force migration without prompts')
    
    def handle(self, *args, **options):
        from_version = options['from_version']
        to_version = options['to_version']
        dry_run = options['dry_run']
        create_backup = options['backup']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"GraphQL Migration: {from_version} → {to_version}"
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Validate versions
        if not self.validate_versions(from_version, to_version):
            raise CommandError("Invalid version combination")
        
        # Check compatibility
        if not self.check_compatibility(from_version, to_version):
            raise CommandError("Incompatible versions")
        
        # Create backup if requested
        if create_backup and not dry_run:
            self.create_backup(from_version)
        
        # Confirm migration
        if not force and not dry_run:
            confirm = input(f"Proceed with migration from {from_version} to {to_version}? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write("Migration cancelled")
                return
        
        # Execute migration
        try:
            self.execute_migration(from_version, to_version, dry_run)
            self.stdout.write(
                self.style.SUCCESS("Migration completed successfully")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Migration failed: {e}")
            )
            raise
    
    def validate_versions(self, from_version, to_version):
        """Validate version format and compatibility."""
        # Implementation depends on your versioning scheme
        return True
    
    def check_compatibility(self, from_version, to_version):
        """Check if migration path is supported."""
        supported_paths = {
            ('1.0', '2.0'): True,
            ('2.0', '2.1'): True,
            ('2.1', '3.0'): True,
            # Add more supported migration paths
        }
        
        return supported_paths.get((from_version, to_version), False)
    
    def create_backup(self, version):
        """Create backup before migration."""
        self.stdout.write("Creating backup...")
        
        # Database backup
        backup_file = f"backup_before_{version}_{int(time.time())}.sql"
        subprocess.run([
            'pg_dump', '-h', 'localhost', '-U', 'graphql_user',
            '-d', 'graphql_db', '-f', backup_file
        ], check=True)
        
        # Code backup
        subprocess.run([
            'tar', '-czf', f"code_backup_before_{version}.tar.gz", '.'
        ], check=True)
        
        self.stdout.write(f"Backup created: {backup_file}")
    
    def execute_migration(self, from_version, to_version, dry_run):
        """Execute the migration process."""
        migration_steps = self.get_migration_steps(from_version, to_version)
        
        for step in migration_steps:
            self.stdout.write(f"Executing: {step['description']}")
            
            if not dry_run:
                step['function']()
            else:
                self.stdout.write(f"  Would execute: {step['command']}")
    
    def get_migration_steps(self, from_version, to_version):
        """Get migration steps for version combination."""
        if from_version == '1.0' and to_version == '2.0':
            return [
                {
                    'description': 'Update package version',
                    'command': 'pip install django-graphql-auto-gen>=2.0.0',
                    'function': lambda: subprocess.run(['pip', 'install', 'django-graphql-auto-gen>=2.0.0'])
                },
                {
                    'description': 'Migrate configuration',
                    'command': 'python manage.py migrate_config --from=1.0 --to=2.0',
                    'function': self.migrate_config_1_0_to_2_0
                },
                {
                    'description': 'Run database migrations',
                    'command': 'python manage.py migrate',
                    'function': lambda: subprocess.run(['python', 'manage.py', 'migrate'])
                },
            ]
        
        return []
    
    def migrate_config_1_0_to_2_0(self):
        """Migrate configuration from v1.0 to v2.0."""
        # Implementation specific to your configuration format
        pass
```

This comprehensive migration guide provides detailed instructions for upgrading between versions of the Django GraphQL Auto-Generation System, including automated tools, testing procedures, and rollback strategies to ensure smooth transitions.