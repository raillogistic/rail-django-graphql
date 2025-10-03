"""Core module for Django GraphQL Auto-Generation.

This module contains the core functionality for automatic GraphQL schema generation,
including configuration management, schema building, error handling, debugging,
and core utilities.
"""

from .config_loader import ConfigLoader
from .schema import SchemaBuilder
from .settings import (
    TypeGeneratorSettings,
    QueryGeneratorSettings,
    MutationGeneratorSettings,
    SchemaSettings,
    GraphQLAutoConfig,
)
from .exceptions import (
    GraphQLAutoError,
    ValidationError,
    AuthenticationError,
    PermissionError,
    ResourceNotFoundError,
    SecurityError,
    RateLimitError,
    QueryComplexityError,
    QueryDepthError,
    FileUploadError,
    ErrorCode,
    ErrorHandler,
    error_handler,
    handle_graphql_error,
)
from .debug import (
    DebugInfo,
    GraphQLDebugMiddleware,
    QueryAnalyzer,
    PerformanceProfiler,
    SchemaIntrospector,
    debug_middleware,
    performance_profiler,
    debug_resolver,
    DebugQuery,
)

__all__ = [
    # Configuration et schéma
    'ConfigLoader',
    'SchemaBuilder', 
    'TypeGeneratorSettings',
    'QueryGeneratorSettings',
    'MutationGeneratorSettings',
    'SchemaSettings',
    'GraphQLAutoConfig',
    
    # Gestion d'erreurs
    'GraphQLAutoError',
    'ValidationError',
    'AuthenticationError',
    'PermissionError',
    'ResourceNotFoundError',
    'SecurityError',
    'RateLimitError',
    'QueryComplexityError',
    'QueryDepthError',
    'FileUploadError',
    'ErrorCode',
    'ErrorHandler',
    'error_handler',
    'handle_graphql_error',
    
    # Debug et profilage
    'DebugInfo',
    'GraphQLDebugMiddleware',
    'QueryAnalyzer',
    'PerformanceProfiler',
    'SchemaIntrospector',
    'debug_middleware',
    'performance_profiler',
    'debug_resolver',
    'DebugQuery',
]