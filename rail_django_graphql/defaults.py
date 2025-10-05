"""
Default settings for rail-django-graphql library.

This module contains all default configuration values for the library.
These can be overridden via Django settings or schema-specific overrides.
"""

from typing import Dict, Any, List, Optional, Tuple

# Library version and metadata
LIBRARY_VERSION = "1.0.0"
LIBRARY_NAME = "rail-django-graphql"

# Core library defaults - organized exactly as documented in settings.md
LIBRARY_DEFAULTS: Dict[str, Any] = {
    # ========================================
    # Core Schema Settings
    # ========================================
    "DEFAULT_SCHEMA": "main",
    "ENABLE_GRAPHIQL": True,
    "GRAPHIQL_TEMPLATE": "graphene/graphiql.html",
    "SCHEMA_ENDPOINT": "/graphql/",
    "AUTHENTICATION_REQUIRED": False,
    "PERMISSION_CLASSES": [],
    "ENABLE_INTROSPECTION": True,
    "ENABLE_PLAYGROUND": True,
    
    # Schema settings (dataclass-compatible) defaults
    "SCHEMA_SETTINGS": {
        "excluded_apps": ["admin", "auth", "contenttypes", "sessions"],
        "excluded_models": [],
        "enable_introspection": True,
        "enable_graphiql": True,
        "auto_refresh_on_model_change": True,
        "enable_pagination": True,
        "auto_camelcase": False,
    },
    
    # ========================================
    # Query Settings
    # ========================================
    "QUERY_SETTINGS": {
        "ENABLE_FILTERING": True,
        "ENABLE_ORDERING": True,
        "ENABLE_PAGINATION": True,
        "DEFAULT_PAGE_SIZE": 20,
        "MAX_PAGE_SIZE": 100,
        "ENABLE_SEARCH": True,
        "SEARCH_FIELDS": ["name", "title", "description"],
        "ENABLE_AGGREGATION": True,
        "ENABLE_DISTINCT": True,
        "ENABLE_RELATED_FIELDS": True,
        "MAX_QUERY_DEPTH": 10,
        "MAX_QUERY_COMPLEXITY": 1000,
        "ENABLE_QUERY_COST_ANALYSIS": True,
        "QUERY_TIMEOUT": 30,  # seconds
    },
    
    # ========================================
    # Mutation Settings
    # ========================================
    "MUTATION_SETTINGS": {
        "ENABLE_CREATE": True,
        "ENABLE_UPDATE": True,
        "ENABLE_DELETE": True,
        "ENABLE_BULK_OPERATIONS": True,
        "MAX_BULK_SIZE": 100,
        "ENABLE_SOFT_DELETE": False,
        "ENABLE_AUDIT_LOG": True,
        "ENABLE_VALIDATION": True,
        "ENABLE_NESTED_MUTATIONS": True,
        "ENABLE_FILE_UPLOADS": True,
        "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
        "ALLOWED_FILE_TYPES": [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf", "text/plain", "text/csv",
            "application/json", "application/xml"
        ],
    },
    
    # ========================================
    # Type Generation Settings
    # ========================================
    "TYPE_SETTINGS": {
        "ENABLE_AUTO_CAMEL_CASE": True,
        "ENABLE_RELAY_NODES": False,
        "ENABLE_CUSTOM_SCALARS": True,
        "ENABLE_ENUM_CHOICES": True,
        "ENABLE_FIELD_DESCRIPTIONS": True,
        "ENABLE_MODEL_DESCRIPTIONS": True,
        "EXCLUDE_FIELDS": ["password", "secret", "token"],
        "INCLUDE_PRIVATE_FIELDS": False,
        "ENABLE_COMPUTED_FIELDS": True,
        "ENABLE_REVERSE_RELATIONS": True,
        "MAX_RELATION_DEPTH": 3,
    },
    
    # ========================================
    # Performance Settings
    # ========================================
    "PERFORMANCE_SETTINGS": {
        "ENABLE_QUERY_OPTIMIZATION": True,
        "ENABLE_SELECT_RELATED": True,
        "ENABLE_PREFETCH_RELATED": True,
        "ENABLE_ONLY_FIELDS": True,
        "ENABLE_DEFER_FIELDS": False,
        "ENABLE_QUERY_CACHING": True,
        "CACHE_TIMEOUT": 300,  # 5 minutes
        "ENABLE_RESULT_CACHING": False,
        "RESULT_CACHE_TIMEOUT": 60,  # 1 minute
        "ENABLE_DATALOADER": True,
        "DATALOADER_CACHE_SIZE": 1000,
    },
    
    # ========================================
    # Security Settings
    # ========================================
    "SECURITY_SETTINGS": {
        "ENABLE_RATE_LIMITING": False,
        "RATE_LIMIT_PER_MINUTE": 60,
        "RATE_LIMIT_PER_HOUR": 1000,
        "ENABLE_QUERY_WHITELIST": False,
        "QUERY_WHITELIST": [],
        "ENABLE_QUERY_BLACKLIST": False,
        "QUERY_BLACKLIST": [],
        "ENABLE_IP_WHITELIST": False,
        "IP_WHITELIST": [],
        "ENABLE_CORS": True,
        "CORS_ALLOW_ALL_ORIGINS": False,
        "CORS_ALLOWED_ORIGINS": [],
    },
    
    # ========================================
    # Error Handling Settings
    # ========================================
    "ERROR_SETTINGS": {
        "ENABLE_DETAILED_ERRORS": True,
        "ENABLE_ERROR_CODES": True,
        "ENABLE_FIELD_ERRORS": True,
        "ENABLE_VALIDATION_ERRORS": True,
        "ENABLE_PERMISSION_ERRORS": True,
        "ENABLE_AUTHENTICATION_ERRORS": True,
        "ENABLE_RATE_LIMIT_ERRORS": True,
        "ERROR_MESSAGE_LANGUAGE": "en",
        "ENABLE_ERROR_LOGGING": True,
        "LOG_LEVEL": "ERROR",
    },
    
    # ========================================
    # Caching Settings
    # ========================================
    "ENABLE_CACHING": False,
    "CACHE_BACKEND": "default",
    "CACHE_TIMEOUT": 300,  # 5 minutes
    "CACHE_KEY_PREFIX": "rail_graphql",
    "CACHE_VERSION": 1,
    "ENABLE_CACHE_INVALIDATION": True,
    "CACHE_INVALIDATION_SIGNALS": True,
    
    # ========================================
    # File Upload Settings
    # ========================================
    "FILE_UPLOAD_SETTINGS": {
        "ENABLE_FILE_UPLOADS": True,
        "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
        "MAX_FILES_PER_REQUEST": 10,
        "ALLOWED_EXTENSIONS": [
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".pdf", ".txt", ".csv", ".json", ".xml"
        ],
        "UPLOAD_PATH": "uploads/",
        "ENABLE_VIRUS_SCANNING": False,
        "ENABLE_IMAGE_PROCESSING": True,
        "IMAGE_THUMBNAIL_SIZES": [(150, 150), (300, 300)],
        "ENABLE_FILE_VALIDATION": True,
    },
    
    # ========================================
    # Monitoring Settings
    # ========================================
    "MONITORING_SETTINGS": {
        "ENABLE_METRICS": False,
        "METRICS_BACKEND": "prometheus",
        "ENABLE_QUERY_LOGGING": False,
        "ENABLE_PERFORMANCE_LOGGING": False,
        "ENABLE_ERROR_TRACKING": False,
        "ERROR_TRACKING_DSN": None,
        "ENABLE_HEALTH_CHECKS": True,
        "HEALTH_CHECK_ENDPOINT": "/health/",
    },
    
    # ========================================
    # Development Settings
    # ========================================
    "DEVELOPMENT_SETTINGS": {
        "ENABLE_DEBUG_MODE": False,
        "ENABLE_QUERY_PROFILING": False,
        "ENABLE_SCHEMA_VALIDATION": True,
        "ENABLE_TYPE_CHECKING": True,
        "ENABLE_DEPRECATION_WARNINGS": True,
        "ENABLE_PERFORMANCE_WARNINGS": True,
    },
    
    # ========================================
    # Schema Registry Settings
    # ========================================
    "SCHEMA_REGISTRY": {
        "ENABLE_AUTO_DISCOVERY": True,
        "DISCOVERY_MODULES": ["models", "schema", "graphql"],
        "ENABLE_SCHEMA_VALIDATION": True,
        "ENABLE_SCHEMA_CACHING": True,
        "SCHEMA_CACHE_TIMEOUT": 3600,  # 1 hour
    },
    
    # ========================================
    # Middleware Settings
    # ========================================
    "MIDDLEWARE_SETTINGS": {
        "ENABLE_PERFORMANCE_MIDDLEWARE": True,
        "ENABLE_AUTHENTICATION_MIDDLEWARE": True,
        "ENABLE_PERMISSION_MIDDLEWARE": True,
        "ENABLE_CACHING_MIDDLEWARE": False,
        "ENABLE_RATE_LIMITING_MIDDLEWARE": False,
        "ENABLE_CORS_MIDDLEWARE": True,
        "ENABLE_ERROR_HANDLING_MIDDLEWARE": True,
    },
    
    # ========================================
    # Extension Settings
    # ========================================
    "EXTENSION_SETTINGS": {
        "ENABLE_AUTH_EXTENSION": True,
        "ENABLE_PERMISSION_EXTENSION": True,
        "ENABLE_CACHING_EXTENSION": True,
        "ENABLE_MONITORING_EXTENSION": False,
        "ENABLE_FILE_EXTENSION": True,
        "ENABLE_HEALTH_EXTENSION": True,
    },
    
    # ========================================
    # Internationalization Settings
    # ========================================
    "I18N_SETTINGS": {
        "ENABLE_I18N": False,
        "DEFAULT_LANGUAGE": "en",
        "SUPPORTED_LANGUAGES": ["en", "fr", "es", "de"],
        "ENABLE_FIELD_TRANSLATION": False,
        "ENABLE_ERROR_TRANSLATION": True,
    },
    
    # ========================================
    # Testing Settings
    # ========================================
    "TESTING_SETTINGS": {
        "ENABLE_TEST_MODE": False,
        "ENABLE_MOCK_DATA": False,
        "ENABLE_FIXTURES": True,
        "ENABLE_FACTORY_BOY": True,
        "ENABLE_COVERAGE": True,
        "COVERAGE_THRESHOLD": 80,
    },
}

# ========================================
# Schema-specific default overrides
# ========================================
SCHEMA_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "admin": {
        "AUTHENTICATION_REQUIRED": True,
        "ENABLE_INTROSPECTION": False,
        "ENABLE_GRAPHIQL": False,
        "PERMISSION_CLASSES": ["rail_django_graphql.permissions.IsAdminUser"],
        "SECURITY_SETTINGS": {
            "ENABLE_RATE_LIMITING": True,
            "RATE_LIMIT_PER_MINUTE": 50,
        },
    },
    "public": {
        "AUTHENTICATION_REQUIRED": False,
        "ENABLE_INTROSPECTION": True,
        "ENABLE_GRAPHIQL": True,
        "QUERY_SETTINGS": {
            "MAX_QUERY_DEPTH": 5,
            "MAX_QUERY_COMPLEXITY": 500,
            "DEFAULT_PAGE_SIZE": 10,
        },
    },
    "api": {
        "AUTHENTICATION_REQUIRED": True,
        "ENABLE_INTROSPECTION": False,
        "ENABLE_GRAPHIQL": False,
        "SECURITY_SETTINGS": {
            "ENABLE_RATE_LIMITING": True,
            "RATE_LIMIT_PER_MINUTE": 100,
        },
    },
    "internal": {
        "AUTHENTICATION_REQUIRED": True,
        "ENABLE_INTROSPECTION": False,
        "QUERY_SETTINGS": {
            "MAX_QUERY_DEPTH": 15,
            "ENABLE_AGGREGATION": True,
        },
    },
}

# ========================================
# Environment-specific defaults
# ========================================
ENVIRONMENT_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "development": {
        "ENABLE_GRAPHIQL": True,
        "ENABLE_INTROSPECTION": True,
        "DEVELOPMENT_SETTINGS": {
            "ENABLE_DEBUG_MODE": True,
            "ENABLE_QUERY_PROFILING": True,
        },
        "ERROR_SETTINGS": {
            "ENABLE_DETAILED_ERRORS": True,
            "LOG_LEVEL": "DEBUG",
        },
    },
    "testing": {
        "ENABLE_GRAPHIQL": False,
        "ENABLE_INTROSPECTION": True,
        "TESTING_SETTINGS": {
            "ENABLE_TEST_MODE": True,
            "ENABLE_MOCK_DATA": True,
        },
    },
    "production": {
        "ENABLE_GRAPHIQL": False,
        "ENABLE_INTROSPECTION": False,
        "DEVELOPMENT_SETTINGS": {
            "ENABLE_DEBUG_MODE": False,
        },
        "SECURITY_SETTINGS": {
            "ENABLE_RATE_LIMITING": True,
            "ENABLE_QUERY_WHITELIST": True,
        },
        "ERROR_SETTINGS": {
            "ENABLE_DETAILED_ERRORS": False,
            "LOG_LEVEL": "ERROR",
        },
    },
}


def get_default_settings() -> Dict[str, Any]:
    """
    Get a copy of the default library settings.
    
    Returns:
        Dict[str, Any]: Copy of LIBRARY_DEFAULTS
    """
    return LIBRARY_DEFAULTS.copy()


def get_schema_defaults(schema_name: str) -> Dict[str, Any]:
    """
    Get default settings for a specific schema.
    
    Args:
        schema_name: Name of the schema to get defaults for
        
    Returns:
        Dict[str, Any]: Schema-specific default settings
    """
    return SCHEMA_DEFAULTS.get(schema_name, {}).copy()


def get_environment_defaults(environment: str) -> Dict[str, Any]:
    """
    Get default settings for a specific environment.
    
    Args:
        environment: Environment name (development, testing, production)
        
    Returns:
        Dict[str, Any]: Environment-specific default settings
    """
    return ENVIRONMENT_DEFAULTS.get(environment, {}).copy()


def merge_settings(*settings_dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple settings dictionaries with deep merging for nested dicts.
    
    This function performs a deep merge where nested dictionaries are merged
    recursively rather than being completely replaced.
    
    Args:
        *settings_dicts: Variable number of settings dictionaries to merge
        
    Returns:
        Dict[str, Any]: Merged settings dictionary
        
    Example:
        >>> base = {"A": {"x": 1, "y": 2}, "B": 3}
        >>> override = {"A": {"y": 20, "z": 30}, "C": 4}
        >>> merge_settings(base, override)
        {"A": {"x": 1, "y": 20, "z": 30}, "B": 3, "C": 4}
    """
    result = {}
    
    for settings_dict in settings_dicts:
        for key, value in settings_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Deep merge nested dictionaries
                result[key] = merge_settings(result[key], value)
            else:
                # Override with new value
                result[key] = value
                
    return result


def get_merged_settings(
    schema_name: Optional[str] = None,
    environment: Optional[str] = None,
    custom_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get merged settings from all sources in priority order.
    
    Priority order (highest to lowest):
    1. custom_settings parameter
    2. schema-specific defaults
    3. environment-specific defaults  
    4. library defaults
    
    Args:
        schema_name: Name of schema for schema-specific defaults
        environment: Environment name for environment-specific defaults
        custom_settings: Custom settings to override defaults
        
    Returns:
        Dict[str, Any]: Merged settings dictionary
    """
    settings_to_merge = [get_default_settings()]
    
    if environment:
        env_defaults = get_environment_defaults(environment)
        if env_defaults:
            settings_to_merge.append(env_defaults)
    
    if schema_name:
        schema_defaults = get_schema_defaults(schema_name)
        if schema_defaults:
            settings_to_merge.append(schema_defaults)
    
    if custom_settings:
        settings_to_merge.append(custom_settings)
    
    return merge_settings(*settings_to_merge)


def validate_settings(settings: Dict[str, Any]) -> List[str]:
    """
    Validate settings configuration and return list of validation errors.
    
    Args:
        settings: Settings dictionary to validate
        
    Returns:
        List[str]: List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate required settings exist
    required_settings = ["DEFAULT_SCHEMA", "SCHEMA_SETTINGS"]
    for setting in required_settings:
        if setting not in settings:
            errors.append(f"Required setting '{setting}' is missing")
    
    # Validate numeric ranges
    if "QUERY_SETTINGS" in settings:
        query_settings = settings["QUERY_SETTINGS"]
        
        if "DEFAULT_PAGE_SIZE" in query_settings and query_settings["DEFAULT_PAGE_SIZE"] <= 0:
            errors.append("DEFAULT_PAGE_SIZE must be greater than 0")
            
        if "MAX_PAGE_SIZE" in query_settings and query_settings["MAX_PAGE_SIZE"] <= 0:
            errors.append("MAX_PAGE_SIZE must be greater than 0")
            
        if ("DEFAULT_PAGE_SIZE" in query_settings and 
            "MAX_PAGE_SIZE" in query_settings and
            query_settings["DEFAULT_PAGE_SIZE"] > query_settings["MAX_PAGE_SIZE"]):
            errors.append("DEFAULT_PAGE_SIZE cannot be greater than MAX_PAGE_SIZE")
    
    # Validate file upload settings
    if "FILE_UPLOAD_SETTINGS" in settings:
        file_settings = settings["FILE_UPLOAD_SETTINGS"]
        
        if "MAX_FILE_SIZE" in file_settings and file_settings["MAX_FILE_SIZE"] <= 0:
            errors.append("MAX_FILE_SIZE must be greater than 0")
    
    return errors