"""
Default settings for rail-django-graphql library.

This module contains all default configuration values for the library.
These can be overridden via Django settings or schema-specific overrides.
"""

from typing import Any, Dict, List, Optional, Tuple

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
    # ========================================
    # Schema Settings (Aligned with SchemaSettings dataclass)
    # ========================================
    "SCHEMA_SETTINGS": {
        # Apps to exclude from schema generation
        "excluded_apps": [],
        # Models to exclude from schema generation
        "excluded_models": [],
        # Enable schema introspection
        "enable_introspection": True,
        # Enable GraphiQL interface
        "enable_graphiql": True,
        # Auto-refresh schema when models change
        "auto_refresh_on_model_change": True,
        # Enable pagination support
        "enable_pagination": True,
        # Enable auto-camelcase for GraphQL schema
        "auto_camelcase": False,
    },
    # ========================================
    # Query Settings (Aligned with QueryGeneratorSettings dataclass)
    # ========================================
    "QUERY_SETTINGS": {
        # Enable filtering support
        "generate_filters": True,
        # Enable ordering support
        "generate_ordering": True,
        # Enable pagination support
        "generate_pagination": True,
        # Enable pagination support (alias for generate_pagination)
        "enable_pagination": True,
        # Enable ordering support (alias for generate_ordering)
        "enable_ordering": True,
        # Enable Relay-style pagination
        "use_relay": False,
        # Default page size for paginated queries
        "default_page_size": 20,
        # Maximum allowed page size
        "max_page_size": 100,
        # Additional fields to use for lookups (e.g., slug, uuid)
        "additional_lookup_fields": {},
    },
    # ========================================
    # Mutation Settings (Enhanced)
    # ========================================
    # Mutation Settings (Aligned with MutationGeneratorSettings dataclass)
    # ========================================
    "MUTATION_SETTINGS": {
        # Enable create mutations
        "generate_create": True,
        # Enable update mutations
        "generate_update": True,
        # Enable delete mutations
        "generate_delete": True,
        # Enable bulk mutations
        "generate_bulk": False,
        # Enable create mutations (alias for generate_create)
        "enable_create": True,
        # Enable update mutations (alias for generate_update)
        "enable_update": True,
        # Enable delete mutations (alias for generate_delete)
        "enable_delete": True,
        # Enable bulk operations
        "enable_bulk_operations": False,
        # Enable method mutations
        "enable_method_mutations": False,
        # Maximum number of items in bulk operations
        "bulk_batch_size": 100,
        # Fields required for update operations
        "required_update_fields": {},
        # Enable/disable nested relationship fields in mutations
        "enable_nested_relations": True,
        # Per-model configuration for nested relations
        "nested_relations_config": {},
        # Per-field configuration for nested relations (model.field -> bool)
        "nested_field_config": {},
    },
    # ========================================
    # Type Generation Settings (DEPRECATED - Use TYPE_GENERATION_SETTINGS)
    # ========================================
    # "TYPE_SETTINGS": {
    #     "ENABLE_AUTO_CAMEL_CASE": True,
    #     "ENABLE_RELAY_NODES": False,
    #     "ENABLE_CUSTOM_SCALARS": True,
    #     "ENABLE_ENUM_CHOICES": True,
    #     "ENABLE_FIELD_DESCRIPTIONS": True,
    #     "ENABLE_MODEL_DESCRIPTIONS": True,
    #     "EXCLUDE_FIELDS": ["password", "secret", "token"],
    #     "INCLUDE_PRIVATE_FIELDS": False,
    #     "ENABLE_COMPUTED_FIELDS": True,
    #     "ENABLE_REVERSE_RELATIONS": True,
    #     "MAX_RELATION_DEPTH": 3,
    # },
    # ========================================
    # Type Generation Settings (Aligned with TypeGeneratorSettings dataclass)
    # ========================================
    "TYPE_GENERATION_SETTINGS": {
        # Fields to exclude from types, per model
        "exclude_fields": {},
        # Alias for exclude_fields
        "excluded_fields": {},
        # Fields to include in types, per model (if None, include all non-excluded fields)
        "include_fields": None,
        # Custom field type mappings
        "custom_field_mappings": {},
        # Enable filter generation for types
        "generate_filters": True,
        # Enable filtering support (alias for generate_filters)
        "enable_filtering": True,
        # Enable auto-camelcase for field names
        "auto_camelcase": False,
        # Enable field descriptions
        "generate_descriptions": True,
    },
    # ========================================
    # Filtering Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "FILTERING": {
    #     "ENABLE_FILTERS": True,
    #     "DEFAULT_FILTER_OPERATORS": {
    #         "CharField": [
    #             "exact",
    #             "icontains",
    #             "startswith",
    #             "endswith",
    #             "iexact",
    #             "contains",
    #             "istartswith",
    #             "iendswith",
    #             "regex",
    #             "iregex",
    #             "in",
    #             "isnull",
    #         ],
    #         "TextField": [
    #             "exact",
    #             "icontains",
    #             "startswith",
    #             "endswith",
    #             "iexact",
    #             "contains",
    #             "istartswith",
    #             "iendswith",
    #             "regex",
    #             "iregex",
    #             "in",
    #             "isnull",
    #         ],
    #         "IntegerField": [
    #             "exact",
    #             "gt",
    #             "gte",
    #             "lt",
    #             "lte",
    #             "range",
    #             "in",
    #             "isnull",
    #         ],
    #         "FloatField": ["exact", "gt", "gte", "lt", "lte", "range", "in", "isnull"],
    #         "DecimalField": [
    #             "exact",
    #             "gt",
    #             "gte",
    #             "lt",
    #             "lte",
    #             "range",
    #             "in",
    #             "isnull",
    #         ],
    #         "BooleanField": ["exact", "isnull"],
    #         "DateTimeField": [
    #             "exact",
    #             "gt",
    #             "gte",
    #             "lt",
    #             "lte",
    #             "range",
    #             "date",
    #             "year",
    #             "month",
    #             "day",
    #             "week",
    #             "week_day",
    #             "quarter",
    #             "time",
    #             "hour",
    #             "minute",
    #             "second",
    #             "isnull",
    #         ],
    #         "DateField": [
    #             "exact",
    #             "gt",
    #             "gte",
    #             "lt",
    #             "lte",
    #             "range",
    #             "year",
    #             "month",
    #             "day",
    #             "week",
    #             "week_day",
    #             "quarter",
    #             "isnull",
    #         ],
    #         "TimeField": [
    #             "exact",
    #             "gt",
    #             "gte",
    #             "lt",
    #             "lte",
    #             "range",
    #             "hour",
    #             "minute",
    #             "second",
    #             "isnull",
    #         ],
    #     },
    #     "ENABLE_LOGICAL_OPERATORS": True,
    #     "ENABLE_RELATIONSHIP_FILTERS": True,
    #     "MAX_FILTER_DEPTH": 3,
    #     "ENABLE_CUSTOM_FILTERS": True,
    #     "CUSTOM_FILTERS": {},
    #     "ENABLE_FILTER_CACHING": True,
    #     "FILTER_CACHE_TIMEOUT": 300,
    #     "FILTER_CACHE_KEY_PREFIX": "graphql_filter",
    # },
    # ========================================
    # Pagination Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "PAGINATION": {
    #     "PAGINATION_SIZE": 20,
    #     "DEFAULT_PAGE_SIZE": 20,
    #     "MAX_PAGE_SIZE": 100,
    #     "USE_RELAY_PAGINATION": False,
    #     "ENABLE_CURSOR_PAGINATION": True,
    #     "ENABLE_OFFSET_PAGINATION": True,
    # },
    # ========================================
    # Performance Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "PERFORMANCE_SETTINGS": {
    #     "ENABLE_QUERY_OPTIMIZATION": True,
    #     "ENABLE_SELECT_RELATED": True,
    #     "ENABLE_PREFETCH_RELATED": True,
    #     "ENABLE_ONLY_FIELDS": True,
    #     "ENABLE_DEFER_FIELDS": False,
    #     "ENABLE_QUERY_CACHING": True,
    #     "CACHE_TIMEOUT": 300,  # 5 minutes
    #     "ENABLE_RESULT_CACHING": False,
    #     "RESULT_CACHE_TIMEOUT": 60,  # 1 minute
    #     "ENABLE_DATALOADER": True,
    #     "DATALOADER_CACHE_SIZE": 1000,
    # },
    # ========================================
    # Security Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "SECURITY": {
    #     "MAX_QUERY_DEPTH": 10,
    #     "MAX_QUERY_COMPLEXITY": 1000,
    #     "QUERY_COST_ANALYSIS": True,
    #     "QUERY_TIMEOUT": 30,
    #     "MUTATION_PERMISSIONS": {},
    #     "SENSITIVE_FIELDS": {},
    #     "FIELD_PERMISSIONS": {},
    #     "ENABLE_RATE_LIMITING": False,
    #     "RATE_LIMIT_PER_MINUTE": 60,
    #     "RATE_LIMIT_PER_HOUR": 1000,
    #     "ENABLE_QUERY_WHITELIST": False,
    #     "QUERY_WHITELIST": [],
    #     "ENABLE_QUERY_BLACKLIST": False,
    #     "QUERY_BLACKLIST": [],
    #     "ENABLE_IP_WHITELIST": False,
    #     "IP_WHITELIST": [],
    #     "ENABLE_CORS": True,
    #     "CORS_ALLOW_ALL_ORIGINS": False,
    #     "CORS_ALLOWED_ORIGINS": [],
    # },
    # ========================================
    # Custom Scalars and Field Converters (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "CUSTOM_SCALARS": {},
    # "FIELD_CONVERTERS": {},
    # ========================================
    # Schema Hooks and Middleware (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "SCHEMA_HOOKS": [],
    # "MIDDLEWARE": [],
    # ========================================
    # Nested Operations Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "NESTED_OPERATIONS": {
    #     "ENABLE_NESTED_CREATE": True,
    #     "ENABLE_NESTED_UPDATE": True,
    #     "ENABLE_NESTED_DELETE": True,
    #     "BULK_THRESHOLD": 10,
    #     "MAX_NESTING_DEPTH": 5,
    #     "ENABLE_QUERY_OPTIMIZATION": True,
    #     "ENABLE_DELETION_SAFETY_CHECKS": True,
    #     "DEFAULT_DELETE_PROTECTION": True,
    #     "REQUIRE_EXPLICIT_CASCADE": True,
    #     "ENABLE_NESTED_VALIDATION": True,
    #     "VALIDATE_RELATIONSHIPS": True,
    #     "STRICT_TYPE_CHECKING": True,
    #     "USE_TRANSACTIONS": True,
    #     "TRANSACTION_ISOLATION_LEVEL": "READ_COMMITTED",
    # },
    # ========================================
    # Relationship Handling Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "RELATIONSHIP_HANDLING": {
    #     "FOREIGN_KEY_ON_DELETE": "protect",
    #     "ONE_TO_MANY_ON_DELETE": "cascade",
    #     "MANY_TO_MANY_ON_DELETE": "clear",
    #     "FOREIGN_KEY_ON_UPDATE": "update",
    #     "ONE_TO_MANY_ON_UPDATE": "merge",
    #     "MANY_TO_MANY_ON_UPDATE": "replace",
    # },
    # ========================================
    # Development Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "DEVELOPMENT": {
    #     "TESTING": False,
    #     "CACHE_ENABLED": True,
    #     "TEST_PAGE_SIZE": 5,
    #     "VERBOSE_LOGGING": True,
    #     "AUTO_RELOAD_SCHEMA": True,
    #     "ENABLE_DEBUG_MODE": False,
    #     "ENABLE_QUERY_PROFILING": False,
    #     "ENABLE_SCHEMA_VALIDATION": True,
    #     "ENABLE_TYPE_CHECKING": True,
    #     "ENABLE_DEPRECATION_WARNINGS": True,
    #     "ENABLE_PERFORMANCE_WARNINGS": True,
    # },
    # ========================================
    # Internationalization Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "I18N": {
    #     "ENABLE_I18N": True,
    #     "SUPPORTED_LANGUAGES": ["fr", "en"],
    #     "DEFAULT_LANGUAGE": "fr",
    #     "TRANSLATABLE_FIELDS": {},
    #     "ENABLE_FIELD_TRANSLATION": False,
    #     "ENABLE_ERROR_TRANSLATION": True,
    # },
    # ========================================
    # Error Handling Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "ERROR_SETTINGS": {
    #     "ENABLE_DETAILED_ERRORS": True,
    #     "ENABLE_ERROR_CODES": True,
    #     "ENABLE_FIELD_ERRORS": True,
    #     "ENABLE_VALIDATION_ERRORS": True,
    #     "ENABLE_PERMISSION_ERRORS": True,
    #     "ENABLE_AUTHENTICATION_ERRORS": True,
    #     "ENABLE_RATE_LIMIT_ERRORS": True,
    #     "ERROR_MESSAGE_LANGUAGE": "en",
    #     "ENABLE_ERROR_LOGGING": True,
    #     "LOG_LEVEL": "ERROR",
    # },
    # ========================================
    # Caching Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "ENABLE_CACHING": False,
    # "CACHE_BACKEND": "default",
    # "CACHE_TIMEOUT": 300,  # 5 minutes
    # "CACHE_KEY_PREFIX": "rail_graphql",
    # "CACHE_VERSION": 1,
    # "ENABLE_CACHE_INVALIDATION": True,
    # "CACHE_INVALIDATION_SIGNALS": True,
    # ========================================
    # File Upload Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "FILE_UPLOAD_SETTINGS": {
    #     "ENABLE_FILE_UPLOADS": True,
    #     "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
    #     "MAX_FILES_PER_REQUEST": 10,
    #     "ALLOWED_EXTENSIONS": [
    #         ".jpg",
    #         ".jpeg",
    #         ".png",
    #         ".gif",
    #         ".webp",
    #         ".pdf",
    #         ".txt",
    #         ".csv",
    #         ".json",
    #         ".xml",
    #     ],
    #     "UPLOAD_PATH": "uploads/",
    #     "ENABLE_VIRUS_SCANNING": False,
    #     "ENABLE_IMAGE_PROCESSING": True,
    #     "IMAGE_THUMBNAIL_SIZES": [(150, 150), (300, 300)],
    #     "ENABLE_FILE_VALIDATION": True,
    # },
    # ========================================
    # Monitoring Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "MONITORING_SETTINGS": {
    #     "ENABLE_METRICS": False,
    #     "METRICS_BACKEND": "prometheus",
    #     "ENABLE_QUERY_LOGGING": False,
    #     "ENABLE_PERFORMANCE_LOGGING": False,
    #     "ENABLE_ERROR_TRACKING": False,
    #     "ERROR_TRACKING_DSN": None,
    #     "ENABLE_HEALTH_CHECKS": True,
    #     "HEALTH_CHECK_ENDPOINT": "/health/",
    # },
    # ========================================
    # Development Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "DEVELOPMENT_SETTINGS": {
    #     "ENABLE_DEBUG_MODE": False,
    #     "ENABLE_QUERY_PROFILING": False,
    #     "ENABLE_SCHEMA_VALIDATION": True,
    #     "ENABLE_TYPE_CHECKING": True,
    #     "ENABLE_DEPRECATION_WARNINGS": True,
    #     "ENABLE_PERFORMANCE_WARNINGS": True,
    # },
    # ========================================
    # Schema Registry Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "SCHEMA_REGISTRY": {
    #     "ENABLE_AUTO_DISCOVERY": True,
    #     "DISCOVERY_MODULES": ["models", "schema", "graphql"],
    #     "ENABLE_SCHEMA_VALIDATION": True,
    #     "ENABLE_SCHEMA_CACHING": True,
    #     "SCHEMA_CACHE_TIMEOUT": 3600,  # 1 hour
    # },
    # ========================================
    # Middleware Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "MIDDLEWARE_SETTINGS": {
    #     "ENABLE_PERFORMANCE_MIDDLEWARE": True,
    #     "ENABLE_AUTHENTICATION_MIDDLEWARE": True,
    #     "ENABLE_PERMISSION_MIDDLEWARE": True,
    #     "ENABLE_CACHING_MIDDLEWARE": False,
    #     "ENABLE_RATE_LIMITING_MIDDLEWARE": False,
    #     "ENABLE_CORS_MIDDLEWARE": True,
    #     "ENABLE_ERROR_HANDLING_MIDDLEWARE": True,
    # },
    # ========================================
    # Extension Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "EXTENSION_SETTINGS": {
    #     "ENABLE_AUTH_EXTENSION": True,
    #     "ENABLE_PERMISSION_EXTENSION": True,
    #     "ENABLE_CACHING_EXTENSION": True,
    #     "ENABLE_MONITORING_EXTENSION": False,
    #     "ENABLE_FILE_EXTENSION": True,
    #     "ENABLE_HEALTH_EXTENSION": True,
    # },
    # ========================================
    # Internationalization Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "I18N_SETTINGS": {
    #     "ENABLE_I18N": False,  # Activer l'internationalisation
    #     "DEFAULT_LANGUAGE": "fr",  # Langue par défaut (français)
    #     "SUPPORTED_LANGUAGES": ["fr", "en", "es", "de"],  # Langues supportées
    #     "ENABLE_FIELD_TRANSLATION": False,  # Activer la traduction des champs
    #     "ENABLE_ERROR_TRANSLATION": True,  # Activer la traduction des erreurs
    #     "FIELD_VERBOSE_NAMES": {
    #         # Noms verbeux en français pour les champs communs
    #         "id": "Identifiant",
    #         "name": "Nom",
    #         "title": "Titre",
    #         "description": "Description",
    #         "created_at": "Créé le",
    #         "updated_at": "Modifié le",
    #         "is_active": "Actif",
    #         "email": "Adresse e-mail",
    #         "phone": "Téléphone",
    #         "address": "Adresse",
    #         "city": "Ville",
    #         "country": "Pays",
    #         "status": "Statut",
    #         "type": "Type",
    #         "category": "Catégorie",
    #         "price": "Prix",
    #         "quantity": "Quantité",
    #         "total": "Total",
    #         "date": "Date",
    #         "time": "Heure",
    #         "user": "Utilisateur",
    #         "author": "Auteur",
    #         "owner": "Propriétaire",
    #     },
    # },
    # ========================================
    # Testing Settings (DEPRECATED - Not defined in dataclasses)
    # ========================================
    # "TESTING_SETTINGS": {
    #     "ENABLE_TEST_MODE": False,
    #     "ENABLE_MOCK_DATA": False,
    #     "ENABLE_FIXTURES": True,
    #     "ENABLE_FACTORY_BOY": True,
    #     "ENABLE_COVERAGE": True,
    #     "COVERAGE_THRESHOLD": 80,
    # },
}

# ========================================
# Schema-specific default overrides (Aligned with dataclass-based settings)
# ========================================
SCHEMA_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "admin": {
        "AUTHENTICATION_REQUIRED": True,
        "ENABLE_INTROSPECTION": False,
        "ENABLE_GRAPHIQL": False,
        "PERMISSION_CLASSES": ["rail_django_graphql.permissions.IsAdminUser"],
    },
    "public": {
        "AUTHENTICATION_REQUIRED": False,
        "ENABLE_INTROSPECTION": True,
        "ENABLE_GRAPHIQL": True,
        "QUERY_SETTINGS": {
            "default_page_size": 10,
        },
    },
    "api": {
        "AUTHENTICATION_REQUIRED": True,
        "ENABLE_INTROSPECTION": False,
        "ENABLE_GRAPHIQL": False,
    },
    "internal": {
        "AUTHENTICATION_REQUIRED": True,
        "ENABLE_INTROSPECTION": False,
    },
}

# ========================================
# Environment-specific defaults (Aligned with dataclass-based settings)
# ========================================
ENVIRONMENT_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "development": {
        "ENABLE_GRAPHIQL": True,
        "ENABLE_INTROSPECTION": True,
    },
    "testing": {
        "ENABLE_GRAPHIQL": False,
        "ENABLE_INTROSPECTION": True,
    },
    "production": {
        "ENABLE_GRAPHIQL": False,
        "ENABLE_INTROSPECTION": False,
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
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Deep merge nested dictionaries
                result[key] = merge_settings(result[key], value)
            else:
                # Override with new value
                result[key] = value

    return result


def get_merged_settings(
    schema_name: Optional[str] = None,
    environment: Optional[str] = None,
    custom_settings: Optional[Dict[str, Any]] = None,
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
    Only validates settings defined in core/settings.py dataclasses.

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

    # Validate numeric ranges for dataclass-defined settings
    if "QUERY_SETTINGS" in settings:
        query_settings = settings["QUERY_SETTINGS"]

        if (
            "default_page_size" in query_settings
            and query_settings["default_page_size"] <= 0
        ):
            errors.append("default_page_size must be greater than 0")

        if "max_page_size" in query_settings and query_settings["max_page_size"] <= 0:
            errors.append("max_page_size must be greater than 0")

        if (
            "default_page_size" in query_settings
            and "max_page_size" in query_settings
            and query_settings["default_page_size"] > query_settings["max_page_size"]
        ):
            errors.append("default_page_size cannot be greater than max_page_size")

    return errors
