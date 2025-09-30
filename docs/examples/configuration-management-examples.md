# Configuration Management Examples

This guide provides practical examples of using the Configuration Management system in django-graphql-auto, including environment-based configuration, feature flags, runtime configuration updates, and validation.

## Table of Contents

1. [Environment-Based Configuration](#environment-based-configuration)
2. [Feature Flags System](#feature-flags-system)
3. [Runtime Configuration Updates](#runtime-configuration-updates)
4. [Configuration Validation](#configuration-validation)
5. [Advanced Use Cases](#advanced-use-cases)

## Environment-Based Configuration

### Basic Environment Setup

```python
# settings/base.py
import os
from pathlib import Path

# Base configuration for all environments
rail_django_graphql = {
    'SCHEMA_CONFIG': {
        'models': ['myapp.models.User', 'myapp.models.Product'],
        'auto_camelcase': True,
        'enable_subscriptions': True,
    },
    'SECURITY_SETTINGS': {
        'max_query_depth': 10,
        'max_query_complexity': 1000,
        'enable_introspection': True,
    },
    'PERFORMANCE_SETTINGS': {
        'enable_query_caching': True,
        'cache_timeout': 300,
        'enable_dataloader': True,
    }
}

# Feature flags base configuration
FEATURE_FLAGS = {
    'enable_advanced_filtering': True,
    'enable_bulk_operations': False,
    'enable_file_uploads': True,
}
```

```python
# settings/development.py
from .base import *

# Development-specific overrides
rail_django_graphql['SECURITY_SETTINGS'].update({
    'enable_introspection': True,
    'enable_graphiql': True,
    'debug_mode': True,
})

rail_django_graphql['PERFORMANCE_SETTINGS'].update({
    'enable_query_caching': False,  # Disable cache for development
    'enable_query_optimization': False,  # Easier debugging
})

# Development feature flags
FEATURE_FLAGS.update({
    'enable_debug_toolbar': True,
    'enable_experimental_features': True,
})
```

```python
# settings/production.py
from .base import *

# Production-specific configuration
rail_django_graphql['SECURITY_SETTINGS'].update({
    'enable_introspection': False,  # Disable in production
    'enable_graphiql': False,
    'max_query_depth': 8,  # Stricter limits
    'enable_rate_limiting': True,
    'rate_limit_per_minute': 100,
})

rail_django_graphql['PERFORMANCE_SETTINGS'].update({
    'enable_query_caching': True,
    'cache_timeout': 600,  # 10 minutes
    'enable_query_optimization': True,
})

# Production feature flags
FEATURE_FLAGS.update({
    'enable_debug_toolbar': False,
    'enable_experimental_features': False,
    'enable_monitoring': True,
})
```

### Loading Environment Configuration

```python
# settings/__init__.py
import os

# Determine environment
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
else:
    from .development import *

# Validate configuration on startup
from rail_django_graphql.core.config_loader import validate_configuration
try:
    validate_configuration()
    print(f"✓ Configuration loaded successfully for {ENVIRONMENT}")
except Exception as e:
    print(f"✗ Configuration error: {e}")
```

## Feature Flags System

### Basic Feature Flags

```python
# settings.py
FEATURE_FLAGS = {
    # Simple boolean flags
    'enable_advanced_search': True,
    'enable_bulk_operations': False,
    'enable_real_time_notifications': True,

    # Advanced feature flag configuration
    'new_user_dashboard': {
        'description': 'New user dashboard with enhanced analytics',
        'type': 'boolean',
        'default_value': False,
        'enabled': True,
        'environments': ['development', 'staging'],
        'percentage_rollout': 25,  # 25% of users
        'dependencies': ['enable_advanced_search'],
        'metadata': {
            'version': '2.1',
            'team': 'frontend',
            'jira_ticket': 'DASH-123'
        }
    },

    # User group-based rollout
    'premium_features': {
        'description': 'Premium features for paid users',
        'type': 'boolean',
        'default_value': False,
        'enabled': True,
        'user_groups': ['premium', 'enterprise'],
        'environments': ['production'],
        'metadata': {
            'billing_required': True
        }
    }
}
```

### Using Feature Flags in Views

```python
# views.py
from rail_django_graphql.core.feature_flags import is_feature_enabled, feature_flag_required
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def user_dashboard(request):
    """User dashboard with conditional features based on flags."""

    # Check feature flag programmatically
    if is_feature_enabled('new_user_dashboard', request.user):
        # Use new dashboard
        return render(request, 'dashboard/new_dashboard.html', {
            'advanced_search': is_feature_enabled('enable_advanced_search', request.user),
            'notifications': is_feature_enabled('enable_real_time_notifications', request.user),
        })
    else:
        # Use legacy dashboard
        return render(request, 'dashboard/legacy_dashboard.html')

@feature_flag_required('enable_bulk_operations')
def bulk_operations_api(request):
    """API endpoint only available when bulk operations are enabled."""
    if request.method == 'POST':
        # Bulk operation logic
        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
```

### Using Feature Flags in GraphQL Resolvers

```python
# resolvers.py
import graphene
from rail_django_graphql.core.feature_flags import is_feature_enabled

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    advanced_user_search = graphene.Field(UserSearchResultType, query=graphene.String())

    def resolve_users(self, info):
        """Standard user list."""
        return User.objects.all()

    def resolve_advanced_user_search(self, info, query):
        """Advanced search only available with feature flag."""
        if not is_feature_enabled('enable_advanced_search', info.context.user):
            raise GraphQLError("Advanced search not available")

        # Advanced search logic
        return perform_advanced_search(query)

class Mutation(graphene.ObjectType):
    bulk_create_users = graphene.Field(BulkCreateResultType, users=graphene.List(UserInputType))

    def resolve_bulk_create_users(self, info, users):
        """Bulk operations with feature flag check."""
        if not is_feature_enabled('enable_bulk_operations', info.context.user):
            return BulkCreateResultType(
                success=False,
                message="Bulk operations not enabled for your account"
            )

        # Bulk creation logic
        return perform_bulk_create(users)
```

### Feature Flag Management Commands

```python
# management/commands/manage_feature_flags.py
from django.core.management.base import BaseCommand
from rail_django_graphql.core.feature_flags import feature_flags

class Command(BaseCommand):
    help = 'Manage feature flags'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['list', 'enable', 'disable', 'status'])
        parser.add_argument('--flag', help='Feature flag name')
        parser.add_argument('--percentage', type=int, help='Rollout percentage')

    def handle(self, *args, **options):
        if options['action'] == 'list':
            self.list_flags()
        elif options['action'] == 'enable':
            self.enable_flag(options['flag'])
        elif options['action'] == 'disable':
            self.disable_flag(options['flag'])
        elif options['action'] == 'status':
            self.show_status(options['flag'])

    def list_flags(self):
        """List all feature flags."""
        all_flags = feature_flags.get_all_flags()
        self.stdout.write("Feature Flags Status:")
        for name, flag in all_flags.items():
            status = "✓ ENABLED" if flag.enabled else "✗ DISABLED"
            self.stdout.write(f"  {name}: {status}")
            if hasattr(flag, 'percentage_rollout'):
                self.stdout.write(f"    Rollout: {flag.percentage_rollout}%")

    def enable_flag(self, flag_name):
        """Enable a feature flag."""
        if feature_flags.enable_flag(flag_name):
            self.stdout.write(f"✓ Enabled flag: {flag_name}")
        else:
            self.stdout.write(f"✗ Failed to enable flag: {flag_name}")
```

## Runtime Configuration Updates

### Basic Runtime Configuration

```python
# utils/config_manager.py
from rail_django_graphql.core.runtime_config import (
    get_runtime_config,
    set_runtime_config,
    runtime_config
)
import logging

logger = logging.getLogger(__name__)

def update_security_settings(max_depth=None, max_complexity=None, user='system'):
    """Update security settings at runtime."""

    if max_depth:
        set_runtime_config(
            'SECURITY_SETTINGS.max_query_depth',
            max_depth,
            user=user,
            reason=f'Security adjustment: depth limit set to {max_depth}'
        )
        logger.info(f"Updated max_query_depth to {max_depth}")

    if max_complexity:
        set_runtime_config(
            'SECURITY_SETTINGS.max_query_complexity',
            max_complexity,
            user=user,
            reason=f'Security adjustment: complexity limit set to {max_complexity}'
        )
        logger.info(f"Updated max_query_complexity to {max_complexity}")

def get_current_limits():
    """Get current security limits."""
    return {
        'max_depth': get_runtime_config('SECURITY_SETTINGS.max_query_depth', 10),
        'max_complexity': get_runtime_config('SECURITY_SETTINGS.max_query_complexity', 1000),
        'rate_limit': get_runtime_config('SECURITY_SETTINGS.rate_limit_per_minute', 60)
    }

def emergency_lockdown(user='admin'):
    """Emergency security lockdown."""
    emergency_settings = {
        'SECURITY_SETTINGS.max_query_depth': 5,
        'SECURITY_SETTINGS.max_query_complexity': 100,
        'SECURITY_SETTINGS.rate_limit_per_minute': 10,
        'SECURITY_SETTINGS.enable_introspection': False,
    }

    for key, value in emergency_settings.items():
        set_runtime_config(key, value, user=user, reason='Emergency lockdown activated')

    logger.critical("Emergency lockdown activated")
```

### Configuration Change Callbacks

```python
# monitoring/config_monitor.py
from rail_django_graphql.core.runtime_config import runtime_config
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def on_security_change(key, old_value, new_value, change_info):
    """Callback for security setting changes."""
    message = f"""
    Security Configuration Change Alert

    Setting: {key}
    Old Value: {old_value}
    New Value: {new_value}
    Changed By: {change_info.get('user', 'Unknown')}
    Reason: {change_info.get('reason', 'No reason provided')}
    Timestamp: {change_info.get('timestamp')}
    """

    # Log the change
    logger.warning(f"Security config changed: {key} = {new_value}")

    # Send email notification
    if hasattr(settings, 'SECURITY_NOTIFICATION_EMAIL'):
        send_mail(
            'Security Configuration Change',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.SECURITY_NOTIFICATION_EMAIL],
            fail_silently=False,
        )

def on_performance_change(key, old_value, new_value, change_info):
    """Callback for performance setting changes."""
    logger.info(f"Performance config changed: {key} = {new_value}")

    # Restart cache if caching settings changed
    if 'cache' in key.lower():
        from django.core.cache import cache
        cache.clear()
        logger.info("Cache cleared due to configuration change")

# Register callbacks
runtime_config.register_change_callback('SECURITY_SETTINGS.*', on_security_change)
runtime_config.register_change_callback('PERFORMANCE_SETTINGS.*', on_performance_change)
```

### Admin Interface for Runtime Configuration

```python
# admin_views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from rail_django_graphql.core.runtime_config import runtime_config, get_runtime_config, set_runtime_config

@staff_member_required
def config_dashboard(request):
    """Admin dashboard for runtime configuration."""

    # Get current configuration
    current_config = {
        'security': {
            'max_query_depth': get_runtime_config('SECURITY_SETTINGS.max_query_depth'),
            'max_query_complexity': get_runtime_config('SECURITY_SETTINGS.max_query_complexity'),
            'rate_limit_per_minute': get_runtime_config('SECURITY_SETTINGS.rate_limit_per_minute'),
        },
        'performance': {
            'enable_query_caching': get_runtime_config('PERFORMANCE_SETTINGS.enable_query_caching'),
            'cache_timeout': get_runtime_config('PERFORMANCE_SETTINGS.cache_timeout'),
            'enable_dataloader': get_runtime_config('PERFORMANCE_SETTINGS.enable_dataloader'),
        }
    }

    # Get change history
    history = runtime_config.get_change_history(limit=20)

    return render(request, 'admin/config_dashboard.html', {
        'current_config': current_config,
        'change_history': history,
    })

@staff_member_required
def update_config_ajax(request):
    """AJAX endpoint for updating configuration."""
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        reason = request.POST.get('reason', 'Admin update')

        try:
            # Convert value to appropriate type
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif '.' in value and value.replace('.', '').isdigit():
                value = float(value)

            # Update configuration
            set_runtime_config(key, value, user=request.user.username, reason=reason)

            return JsonResponse({
                'success': True,
                'message': f'Updated {key} to {value}'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})
```

## Configuration Validation

### Custom Validation Rules

```python
# validators/config_validators.py
from rail_django_graphql.core.runtime_config import runtime_config
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class ConfigurationValidator:
    """Custom configuration validator with business rules."""

    def __init__(self):
        self.validation_rules = {
            'SECURITY_SETTINGS.max_query_depth': self.validate_query_depth,
            'SECURITY_SETTINGS.max_query_complexity': self.validate_query_complexity,
            'PERFORMANCE_SETTINGS.cache_timeout': self.validate_cache_timeout,
        }

    def validate_query_depth(self, value):
        """Validate query depth limits."""
        if not isinstance(value, int):
            raise ValidationError("Query depth must be an integer")

        if value < 1:
            raise ValidationError("Query depth must be at least 1")

        if value > 20:
            raise ValidationError("Query depth cannot exceed 20 for performance reasons")

        return True

    def validate_query_complexity(self, value):
        """Validate query complexity limits."""
        if not isinstance(value, int):
            raise ValidationError("Query complexity must be an integer")

        if value < 100:
            raise ValidationError("Query complexity must be at least 100")

        if value > 10000:
            raise ValidationError("Query complexity cannot exceed 10000")

        return True

    def validate_cache_timeout(self, value):
        """Validate cache timeout settings."""
        if not isinstance(value, int):
            raise ValidationError("Cache timeout must be an integer")

        if value < 0:
            raise ValidationError("Cache timeout cannot be negative")

        if value > 3600:  # 1 hour
            logger.warning(f"Cache timeout {value}s is very high, consider reducing")

        return True

    def validate_config(self, key, value):
        """Validate a configuration value."""
        if key in self.validation_rules:
            return self.validation_rules[key](value)
        return True

# Register validator with runtime config
validator = ConfigurationValidator()
runtime_config.add_validator(validator.validate_config)
```

### Validation in Management Commands

```python
# management/commands/validate_config.py
from django.core.management.base import BaseCommand
from rail_django_graphql.core.config_loader import validate_configuration, debug_configuration
from rail_django_graphql.core.runtime_config import runtime_config

class Command(BaseCommand):
    help = 'Validate current configuration'

    def add_arguments(self, parser):
        parser.add_argument('--debug', action='store_true', help='Show debug information')
        parser.add_argument('--fix', action='store_true', help='Attempt to fix common issues')

    def handle(self, *args, **options):
        self.stdout.write("Validating configuration...")

        try:
            # Validate base configuration
            is_valid = validate_configuration()

            if is_valid:
                self.stdout.write(self.style.SUCCESS("✓ Base configuration is valid"))
            else:
                self.stdout.write(self.style.ERROR("✗ Base configuration has errors"))

            # Validate runtime configuration
            runtime_errors = runtime_config.validate_config()

            if not runtime_errors:
                self.stdout.write(self.style.SUCCESS("✓ Runtime configuration is valid"))
            else:
                self.stdout.write(self.style.ERROR("✗ Runtime configuration errors:"))
                for key, errors in runtime_errors.items():
                    for error in errors:
                        self.stdout.write(f"  {key}: {error}")

            # Show debug information if requested
            if options['debug']:
                self.stdout.write("\nDebug Information:")
                debug_configuration()

            # Attempt fixes if requested
            if options['fix'] and runtime_errors:
                self.attempt_fixes(runtime_errors)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Validation failed: {e}"))

    def attempt_fixes(self, errors):
        """Attempt to fix common configuration issues."""
        self.stdout.write("\nAttempting to fix configuration issues...")

        fixes_applied = 0
        for key, error_list in errors.items():
            for error in error_list:
                if "must be an integer" in error and key.endswith('max_query_depth'):
                    runtime_config.set_config(key, 10, user='auto-fix', reason='Fixed invalid type')
                    fixes_applied += 1
                    self.stdout.write(f"  Fixed {key}: set to default value 10")

        if fixes_applied:
            self.stdout.write(self.style.SUCCESS(f"Applied {fixes_applied} fixes"))
        else:
            self.stdout.write("No automatic fixes available")
```

## Advanced Use Cases

### A/B Testing with Feature Flags

```python
# ab_testing.py
from rail_django_graphql.core.feature_flags import is_feature_enabled
from django.contrib.auth.models import User
import hashlib

class ABTestManager:
    """Manage A/B tests using feature flags."""

    def __init__(self):
        self.tests = {
            'new_checkout_flow': {
                'flag': 'enable_new_checkout',
                'percentage': 50,
                'metric': 'conversion_rate'
            },
            'enhanced_search': {
                'flag': 'enable_enhanced_search',
                'percentage': 25,
                'metric': 'search_success_rate'
            }
        }

    def is_user_in_test(self, test_name, user):
        """Determine if user is in A/B test group."""
        if test_name not in self.tests:
            return False

        test_config = self.tests[test_name]

        # Check if feature flag is enabled
        if not is_feature_enabled(test_config['flag'], user):
            return False

        # Use consistent hashing for user assignment
        user_hash = hashlib.md5(f"{test_name}:{user.id}".encode()).hexdigest()
        hash_value = int(user_hash[:8], 16) % 100

        return hash_value < test_config['percentage']

    def get_variant(self, test_name, user):
        """Get A/B test variant for user."""
        if self.is_user_in_test(test_name, user):
            return 'variant_b'
        return 'variant_a'

# Usage in views
ab_test = ABTestManager()

def checkout_view(request):
    variant = ab_test.get_variant('new_checkout_flow', request.user)

    if variant == 'variant_b':
        return render(request, 'checkout/new_checkout.html')
    else:
        return render(request, 'checkout/standard_checkout.html')
```

### Configuration Monitoring and Alerting

```python
# monitoring/config_monitor.py
from rail_django_graphql.core.runtime_config import runtime_config
from django.core.cache import cache
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

class ConfigurationMonitor:
    """Monitor configuration changes and system health."""

    def __init__(self):
        self.alert_thresholds = {
            'config_changes_per_hour': 10,
            'failed_validations_per_hour': 5,
        }
        self.setup_monitoring()

    def setup_monitoring(self):
        """Set up configuration monitoring."""
        # Register change callbacks
        runtime_config.register_change_callback('*', self.on_any_config_change)

        # Set up periodic health checks
        self.schedule_health_checks()

    def on_any_config_change(self, key, old_value, new_value, change_info):
        """Monitor all configuration changes."""
        # Record change
        self.record_change(key, old_value, new_value, change_info)

        # Check for suspicious activity
        if self.is_suspicious_change(key, change_info):
            self.alert_suspicious_activity(key, change_info)

        # Update metrics
        self.update_change_metrics()

    def record_change(self, key, old_value, new_value, change_info):
        """Record configuration change for analysis."""
        change_record = {
            'timestamp': timezone.now().isoformat(),
            'key': key,
            'old_value': str(old_value),
            'new_value': str(new_value),
            'user': change_info.get('user', 'unknown'),
            'reason': change_info.get('reason', ''),
        }

        # Store in cache for recent changes
        recent_changes = cache.get('config_recent_changes', [])
        recent_changes.append(change_record)

        # Keep only last 100 changes
        if len(recent_changes) > 100:
            recent_changes = recent_changes[-100:]

        cache.set('config_recent_changes', recent_changes, 3600)  # 1 hour

        # Log change
        logger.info(f"Config change: {key} = {new_value} by {change_info.get('user')}")

    def is_suspicious_change(self, key, change_info):
        """Detect suspicious configuration changes."""
        # Check for security-related changes
        if 'SECURITY_SETTINGS' in key:
            # Security changes outside business hours
            current_hour = timezone.now().hour
            if current_hour < 8 or current_hour > 18:
                return True

            # Changes by non-admin users
            user = change_info.get('user', '')
            if user and not user.endswith('_admin'):
                return True

        return False

    def alert_suspicious_activity(self, key, change_info):
        """Alert on suspicious configuration changes."""
        alert_message = f"""
        SUSPICIOUS CONFIGURATION CHANGE DETECTED

        Key: {key}
        User: {change_info.get('user', 'Unknown')}
        Time: {timezone.now()}
        Reason: {change_info.get('reason', 'No reason provided')}
        """

        logger.critical(alert_message)

        # Send to monitoring system
        self.send_alert('suspicious_config_change', alert_message)

    def update_change_metrics(self):
        """Update configuration change metrics."""
        current_hour = timezone.now().strftime('%Y-%m-%d-%H')
        cache_key = f'config_changes_hour_{current_hour}'

        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, 3600)

        # Check threshold
        if current_count + 1 > self.alert_thresholds['config_changes_per_hour']:
            self.send_alert('high_config_change_rate',
                          f'High configuration change rate: {current_count + 1} changes this hour')

    def send_alert(self, alert_type, message):
        """Send alert to monitoring system."""
        # Implementation depends on your monitoring system
        # Could be Slack, email, PagerDuty, etc.
        logger.critical(f"ALERT [{alert_type}]: {message}")

# Initialize monitor
config_monitor = ConfigurationMonitor()
```

### Configuration Templates

```python
# templates/config_templates.py
from rail_django_graphql.core.runtime_config import set_runtime_config

class ConfigurationTemplates:
    """Pre-defined configuration templates for common scenarios."""

    @staticmethod
    def apply_high_security_template(user='admin'):
        """Apply high security configuration template."""
        security_config = {
            'SECURITY_SETTINGS.max_query_depth': 5,
            'SECURITY_SETTINGS.max_query_complexity': 500,
            'SECURITY_SETTINGS.rate_limit_per_minute': 30,
            'SECURITY_SETTINGS.enable_introspection': False,
            'SECURITY_SETTINGS.enable_graphiql': False,
            'SECURITY_SETTINGS.require_authentication': True,
        }

        for key, value in security_config.items():
            set_runtime_config(key, value, user=user, reason='High security template applied')

    @staticmethod
    def apply_high_performance_template(user='admin'):
        """Apply high performance configuration template."""
        performance_config = {
            'PERFORMANCE_SETTINGS.enable_query_caching': True,
            'PERFORMANCE_SETTINGS.cache_timeout': 900,  # 15 minutes
            'PERFORMANCE_SETTINGS.enable_dataloader': True,
            'PERFORMANCE_SETTINGS.enable_query_optimization': True,
            'PERFORMANCE_SETTINGS.max_page_size': 50,
        }

        for key, value in performance_config.items():
            set_runtime_config(key, value, user=user, reason='High performance template applied')

    @staticmethod
    def apply_development_template(user='admin'):
        """Apply development-friendly configuration template."""
        dev_config = {
            'SECURITY_SETTINGS.enable_introspection': True,
            'SECURITY_SETTINGS.enable_graphiql': True,
            'SECURITY_SETTINGS.max_query_depth': 15,
            'PERFORMANCE_SETTINGS.enable_query_caching': False,
            'PERFORMANCE_SETTINGS.enable_query_optimization': False,
        }

        for key, value in dev_config.items():
            set_runtime_config(key, value, user=user, reason='Development template applied')

# Usage
def emergency_security_lockdown():
    """Apply emergency security settings."""
    ConfigurationTemplates.apply_high_security_template(user='emergency_system')

def optimize_for_high_traffic():
    """Optimize configuration for high traffic periods."""
    ConfigurationTemplates.apply_high_performance_template(user='auto_optimizer')
```

## Best Practices

### 1. Configuration Hierarchy

```python
# Use clear configuration hierarchy
rail_django_graphql = {
    'SCHEMA_CONFIG': {...},      # Schema generation settings
    'SECURITY_SETTINGS': {...},  # Security-related settings
    'PERFORMANCE_SETTINGS': {...}, # Performance optimization
    'FEATURE_FLAGS': {...},      # Feature toggles
}
```

### 2. Environment-Specific Settings

```python
# Always use environment-specific configurations
# settings/base.py - Common settings
# settings/development.py - Development overrides
# settings/production.py - Production overrides
```

### 3. Feature Flag Naming

```python
# Use descriptive, hierarchical naming
FEATURE_FLAGS = {
    'api_v2_enabled': True,
    'ui_new_dashboard': False,
    'billing_stripe_integration': True,
    'analytics_advanced_tracking': False,
}
```

### 4. Configuration Validation

```python
# Always validate configuration changes
def update_config_safely(key, value, user):
    try:
        # Validate first
        runtime_config.validate_config({key: value})

        # Apply change
        set_runtime_config(key, value, user=user)

        return True
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False
```

### 5. Monitoring and Alerting

```python
# Monitor critical configuration changes
runtime_config.register_change_callback(
    'SECURITY_SETTINGS.*',
    send_security_alert
)
```

This comprehensive guide demonstrates how to effectively use the Configuration Management system in django-graphql-auto for various scenarios, from basic environment setup to advanced monitoring and A/B testing.
