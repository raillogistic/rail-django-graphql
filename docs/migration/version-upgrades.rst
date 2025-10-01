Version Upgrades
================

This guide covers upgrading Django GraphQL Auto between major and minor versions.

.. contents:: Table of Contents
   :local:
   :depth: 2

Upgrade Overview
---------------

Semantic Versioning
~~~~~~~~~~~~~~~~~~

Django GraphQL Auto follows `Semantic Versioning <https://semver.org/>`_:

* **Major versions** (e.g., 1.0.0 → 2.0.0): Breaking changes
* **Minor versions** (e.g., 1.1.0 → 1.2.0): New features, backward compatible
* **Patch versions** (e.g., 1.1.0 → 1.1.1): Bug fixes, backward compatible

Pre-Upgrade Checklist
~~~~~~~~~~~~~~~~~~~~

Before upgrading, ensure you have:

1. **Backup your database** and codebase
2. **Review the changelog** for breaking changes
3. **Test in a staging environment** first
4. **Update dependencies** to compatible versions
5. **Check deprecation warnings** in current version

.. code-block:: bash

   # Create database backup
   python manage.py dumpdata > backup_$(date +%Y%m%d).json
   
   # Or use database-specific tools
   pg_dump mydb > backup_$(date +%Y%m%d).sql

Upgrading to Version 2.x
------------------------

Breaking Changes in 2.0
~~~~~~~~~~~~~~~~~~~~~~

**Schema Definition Changes**

Version 2.0 introduces a new schema definition syntax:

.. code-block:: python

   # OLD (v1.x)
   from django_graphql_auto import GraphQLAutoSchema
   
   schema = GraphQLAutoSchema(
       models=[User, Post, Comment],
       permissions={'User': ['read', 'create']}
   )

.. code-block:: python

   # NEW (v2.x)
   from django_graphql_auto import AutoSchema
   from django_graphql_auto.decorators import graphql_model
   
   @graphql_model(permissions=['read', 'create'])
   class User(models.Model):
       # model definition
   
   schema = AutoSchema.build()

**Configuration Changes**

Settings structure has been updated:

.. code-block:: python

   # OLD (v1.x)
   GRAPHQL_AUTO = {
       'SCHEMA_PATH': 'myapp.schema',
       'MAX_QUERY_DEPTH': 10,
       'ENABLE_INTROSPECTION': True,
   }

.. code-block:: python

   # NEW (v2.x)
   DJANGO_GRAPHQL_AUTO = {
       'SCHEMA': {
           'AUTO_DISCOVER': True,
           'MAX_QUERY_DEPTH': 10,
           'MAX_QUERY_COMPLEXITY': 1000,
       },
       'INTROSPECTION': {
           'ENABLED': True,
           'DEPTH_LIMIT': 5,
       },
       'PERMISSIONS': {
           'DEFAULT_POLICY': 'deny',
           'CACHE_TIMEOUT': 300,
       }
   }

**Permission System Overhaul**

The permission system has been completely redesigned:

.. code-block:: python

   # OLD (v1.x)
   from django_graphql_auto.permissions import ModelPermission
   
   class UserPermission(ModelPermission):
       def has_permission(self, user, action):
           return user.is_authenticated

.. code-block:: python

   # NEW (v2.x)
   from django_graphql_auto.permissions import BasePermission
   
   class UserPermission(BasePermission):
       def has_object_permission(self, info, obj, action):
           return info.context.user.is_authenticated
       
       def filter_queryset(self, info, queryset, action):
           if not info.context.user.is_staff:
               return queryset.filter(is_active=True)
           return queryset

Migration Steps for 2.0
~~~~~~~~~~~~~~~~~~~~~~

**Step 1: Update Dependencies**

.. code-block:: bash

   pip install django-graphql-auto>=2.0.0

**Step 2: Update Settings**

Create a migration script:

.. code-block:: python

   # migrate_settings.py
   import os
   import re
   
   def migrate_settings():
       """Migrate v1.x settings to v2.x format"""
       settings_file = 'myproject/settings.py'
       
       with open(settings_file, 'r') as f:
           content = f.read()
       
       # Replace old setting name
       content = re.sub(
           r'GRAPHQL_AUTO\s*=',
           'DJANGO_GRAPHQL_AUTO =',
           content
       )
       
       # Update structure (manual review required)
       print("Manual review required for settings structure")
       
       with open(settings_file, 'w') as f:
           f.write(content)
   
   if __name__ == '__main__':
       migrate_settings()

**Step 3: Update Schema Definitions**

.. code-block:: python

   # migrate_schema.py
   import ast
   import os
   
   def migrate_schema_files():
       """Convert old schema definitions to new format"""
       for root, dirs, files in os.walk('.'):
           for file in files:
               if file.endswith('.py'):
                   filepath = os.path.join(root, file)
                   migrate_file(filepath)
   
   def migrate_file(filepath):
       with open(filepath, 'r') as f:
           content = f.read()
       
       # Replace imports
       content = content.replace(
           'from django_graphql_auto import GraphQLAutoSchema',
           'from django_graphql_auto import AutoSchema'
       )
       
       # Add decorator imports
       if 'GraphQLAutoSchema' in content:
           content = 'from django_graphql_auto.decorators import graphql_model\n' + content
       
       with open(filepath, 'w') as f:
           f.write(content)

**Step 4: Update Model Decorators**

.. code-block:: python

   # Before (v1.x)
   class User(models.Model):
       name = models.CharField(max_length=100)
       email = models.EmailField()

.. code-block:: python

   # After (v2.x)
   from django_graphql_auto.decorators import graphql_model
   
   @graphql_model(
       permissions=['read', 'create', 'update'],
       fields=['name', 'email'],
       exclude_fields=['password']
   )
   class User(models.Model):
       name = models.CharField(max_length=100)
       email = models.EmailField()
       password = models.CharField(max_length=128)

**Step 5: Update Permission Classes**

.. code-block:: python

   # migration_permissions.py
   def migrate_permissions():
       """Convert v1.x permissions to v2.x format"""
       
       # Old permission class
       old_permission = '''
   class UserPermission(ModelPermission):
       def has_permission(self, user, action):
           return user.is_authenticated
       '''
       
       # New permission class
       new_permission = '''
   class UserPermission(BasePermission):
       def has_object_permission(self, info, obj, action):
           return info.context.user.is_authenticated
       
       def filter_queryset(self, info, queryset, action):
           return queryset
       '''
       
       print("Manual conversion required for permission classes")
       print("Old format:", old_permission)
       print("New format:", new_permission)

**Step 6: Run Tests**

.. code-block:: bash

   # Run comprehensive tests
   python manage.py test
   
   # Check for deprecation warnings
   python -Wd manage.py test

Upgrading to Version 1.6
------------------------

New Features in 1.6
~~~~~~~~~~~~~~~~~~

* Enhanced query optimization
* Improved error handling
* New middleware system
* Better caching support

Migration Steps for 1.6
~~~~~~~~~~~~~~~~~~~~~~

**Step 1: Update Package**

.. code-block:: bash

   pip install django-graphql-auto>=1.6.0,<2.0.0

**Step 2: Update Middleware (Optional)**

.. code-block:: python

   # settings.py
   MIDDLEWARE = [
       # ... other middleware
       'django_graphql_auto.middleware.GraphQLMiddleware',  # New in 1.6
       # ... rest of middleware
   ]

**Step 3: Enable New Caching (Optional)**

.. code-block:: python

   # settings.py
   DJANGO_GRAPHQL_AUTO = {
       'CACHING': {
           'ENABLED': True,
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'TIMEOUT': 300,
       }
   }

Upgrading to Version 1.5
------------------------

New Features in 1.5
~~~~~~~~~~~~~~~~~~

* Subscription support
* Real-time updates
* WebSocket integration
* Enhanced filtering

Migration Steps for 1.5
~~~~~~~~~~~~~~~~~~~~~~

**Step 1: Update Package**

.. code-block:: bash

   pip install django-graphql-auto>=1.5.0,<1.6.0

**Step 2: Add Channels (for Subscriptions)**

.. code-block:: bash

   pip install channels channels-redis

**Step 3: Update Settings**

.. code-block:: python

   # settings.py
   INSTALLED_APPS = [
       # ... other apps
       'channels',
       'django_graphql_auto',
   ]
   
   ASGI_APPLICATION = 'myproject.asgi.application'
   
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               'hosts': [('127.0.0.1', 6379)],
           },
       },
   }

**Step 4: Update ASGI Configuration**

.. code-block:: python

   # asgi.py
   import os
   from django.core.asgi import get_asgi_application
   from channels.routing import ProtocolTypeRouter, URLRouter
   from channels.auth import AuthMiddlewareStack
   from django_graphql_auto.routing import websocket_urlpatterns
   
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
   
   application = ProtocolTypeRouter({
       'http': get_asgi_application(),
       'websocket': AuthMiddlewareStack(
           URLRouter(websocket_urlpatterns)
       ),
   })

Common Upgrade Issues
--------------------

Import Errors
~~~~~~~~~~~

**Problem**: Import errors after upgrade

.. code-block:: python

   ImportError: cannot import name 'GraphQLAutoSchema' from 'django_graphql_auto'

**Solution**: Update import statements

.. code-block:: python

   # Check version-specific imports
   try:
       from django_graphql_auto import AutoSchema  # v2.x
   except ImportError:
       from django_graphql_auto import GraphQLAutoSchema as AutoSchema  # v1.x

Schema Generation Errors
~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Schema fails to generate after upgrade

.. code-block:: bash

   django.core.exceptions.ImproperlyConfigured: Schema configuration error

**Solution**: Validate configuration

.. code-block:: python

   # validate_schema.py
   from django.core.management.base import BaseCommand
   from django_graphql_auto import AutoSchema
   
   class Command(BaseCommand):
       def handle(self, *args, **options):
           try:
               schema = AutoSchema.build()
               self.stdout.write("Schema validation successful")
           except Exception as e:
               self.stderr.write(f"Schema validation failed: {e}")

Permission Errors
~~~~~~~~~~~~~~~

**Problem**: Permission system not working after upgrade

.. code-block:: bash

   PermissionDenied: Access denied for operation

**Solution**: Update permission classes

.. code-block:: python

   # Check permission class compatibility
   from django_graphql_auto.permissions import BasePermission
   
   class DebugPermission(BasePermission):
       def has_object_permission(self, info, obj, action):
           print(f"Permission check: {action} on {obj}")
           return True  # Allow all for debugging

Database Migration Issues
~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Database migrations fail after upgrade

.. code-block:: bash

   django.db.migrations.exceptions.InconsistentMigrationHistory

**Solution**: Create custom migration

.. code-block:: python

   # Create migration file
   python manage.py makemigrations --empty myapp
   
   # Edit migration file
   from django.db import migrations
   
   class Migration(migrations.Migration):
       dependencies = [
           ('myapp', '0001_initial'),
       ]
       
       operations = [
           # Add custom migration operations
       ]

Testing Upgrades
---------------

Automated Testing
~~~~~~~~~~~~~~~

.. code-block:: python

   # test_upgrade.py
   import unittest
   from django.test import TestCase
   from django_graphql_auto import AutoSchema
   
   class UpgradeTestCase(TestCase):
       def test_schema_generation(self):
           """Test that schema generates without errors"""
           try:
               schema = AutoSchema.build()
               self.assertIsNotNone(schema)
           except Exception as e:
               self.fail(f"Schema generation failed: {e}")
       
       def test_basic_query(self):
           """Test basic GraphQL query functionality"""
           query = '''
           query {
               users {
                   id
                   name
               }
           }
           '''
           # Execute query and validate response
           
       def test_permissions(self):
           """Test permission system functionality"""
           # Test various permission scenarios

Manual Testing Checklist
~~~~~~~~~~~~~~~~~~~~~~~

1. **Schema Introspection**: Verify schema structure
2. **Basic Queries**: Test CRUD operations
3. **Permissions**: Verify access control
4. **Performance**: Check query performance
5. **Error Handling**: Test error scenarios

.. code-block:: bash

   # Manual testing commands
   python manage.py graphql_schema --print
   python manage.py test_graphql_queries
   python manage.py check_permissions

Rollback Procedures
------------------

Version Rollback
~~~~~~~~~~~~~~

If upgrade fails, rollback to previous version:

.. code-block:: bash

   # Rollback package
   pip install django-graphql-auto==1.5.2
   
   # Restore database backup
   python manage.py loaddata backup_20231201.json
   
   # Restore code from version control
   git checkout previous-working-commit

Database Rollback
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Django migrations rollback
   python manage.py migrate myapp 0001
   
   # Or restore from database backup
   psql mydb < backup_20231201.sql

Configuration Rollback
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Keep backup of settings
   # settings_backup.py
   DJANGO_GRAPHQL_AUTO_BACKUP = {
       # Previous working configuration
   }
   
   # Restore in settings.py
   DJANGO_GRAPHQL_AUTO = DJANGO_GRAPHQL_AUTO_BACKUP

Best Practices
---------------

Upgrade Strategy
~~~~~~~~~~~~~~~~

1. **Staged Rollout**: Upgrade in stages (dev → staging → production)
2. **Feature Flags**: Use feature flags for new functionality
3. **Monitoring**: Monitor application health during upgrade
4. **Documentation**: Document all changes and customizations
5. **Team Communication**: Inform team about breaking changes

Version Pinning
~~~~~~~~~~~~~~~

.. code-block:: bash

   # requirements.txt
   django-graphql-auto==2.1.0  # Pin exact version for production
   
   # requirements-dev.txt
   django-graphql-auto>=2.1.0,<3.0.0  # Allow minor updates in development

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # .github/workflows/upgrade-test.yml
   name: Upgrade Test
   on:
     schedule:
       - cron: '0 2 * * 1'  # Weekly on Monday
   
   jobs:
     test-upgrade:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Test Latest Version
           run: |
             pip install django-graphql-auto --upgrade
             python manage.py test
             python manage.py check

Support and Resources
---------------------

Getting Help
~~~~~~~~~~~~

* **Documentation**: https://django-graphql-auto.readthedocs.io/
* **GitHub Issues**: https://github.com/django-graphql-auto/django-graphql-auto/issues
* **Community Forum**: https://forum.django-graphql-auto.org/
* **Stack Overflow**: Tag questions with `django-graphql-auto`

Migration Tools
~~~~~~~~~~~~~~~

* **Schema Validator**: Built-in schema validation
* **Configuration Migrator**: Automated settings migration
* **Permission Converter**: Permission class conversion tool
* **Test Suite**: Comprehensive upgrade test suite

Professional Support
~~~~~~~~~~~~~~~~~~~~

For enterprise customers:

* **Priority Support**: Dedicated support channel
* **Migration Assistance**: Professional migration services
* **Custom Training**: Team training on new features
* **SLA Guarantees**: Service level agreements