"""
Django GraphQL Auto - Génération automatique de schémas GraphQL pour Django.

Ce package fournit des outils pour générer automatiquement des schémas GraphQL
à partir de modèles Django avec des fonctionnalités avancées de sécurité,
de permissions et d'optimisation des performances.
"""

__version__ = "1.0.0"
__author__ = "Django GraphQL Auto Team"
__email__ = "contact@django-graphql-auto.com"

# Imports principaux
from .core.schema_generator import SchemaGenerator
from .core.type_registry import TypeRegistry
from .generators.types import TypeGenerator
from .generators.queries import QueryGenerator
from .generators.mutations import MutationGenerator
from .security.permissions import PermissionChecker
from .security.field_permissions import FieldPermissionChecker

# Imports d'optimisation des performances
from .extensions.optimization import (
    QueryOptimizer,
    QueryAnalyzer,
    PerformanceMonitor,
    QueryOptimizationConfig,
    get_optimizer,
    get_performance_monitor,
    optimize_query
)
from .extensions.caching import (
    GraphQLCacheManager,
    CacheConfig,
    get_cache_manager,
    cache_query,
    cache_field
)

# Imports de gestion des fichiers et médias
from .generators.file_uploads import (
    FileUploadGenerator,
    FileInfo,
    FileUploadResult,
    MultipleFileUploadResult,
    FileValidator,
    FileProcessor
)
from .extensions.media import (
    MediaManager,
    ImageProcessor,
    ThumbnailSize,
    MediaInfo,
    ThumbnailInfo,
    StorageBackend,
    LocalStorageBackend,
    S3StorageBackend,
    CDNManager
)
from .extensions.virus_scanner import (
    VirusScanner,
    ClamAVScanner,
    MockScanner,
    ScanResult,
    ThreatDetected
)
from .middleware.performance import (
    GraphQLPerformanceMiddleware,
    GraphQLPerformanceView,
    get_performance_aggregator,
    setup_performance_monitoring,
    monitor_performance
)

# Configuration par défaut
default_app_config = 'django_graphql_auto.apps.DjangoGraphQLAutoConfig'

__all__ = [
    # Core components
    'SchemaGenerator',
    'TypeRegistry',
    'TypeGenerator',
    'QueryGenerator',
    'MutationGenerator',
    
    # Security components
    'PermissionChecker',
    'FieldPermissionChecker',
    
    # Performance optimization components
    'QueryOptimizer',
    'QueryAnalyzer',
    'PerformanceMonitor',
    'QueryOptimizationConfig',
    'get_optimizer',
    'get_performance_monitor',
    'optimize_query',
    
    # Caching components
    'GraphQLCacheManager',
    'CacheConfig',
    'get_cache_manager',
    'cache_query',
    'cache_field',
    
    # File upload and media components
    'FileUploadGenerator',
    'FileInfo',
    'FileUploadResult',
    'MultipleFileUploadResult',
    'FileValidator',
    'FileProcessor',
    'MediaManager',
    'ImageProcessor',
    'ThumbnailSize',
    'MediaInfo',
    'ThumbnailInfo',
    'StorageBackend',
    'LocalStorageBackend',
    'S3StorageBackend',
    'CDNManager',
    'VirusScanner',
    'ClamAVScanner',
    'MockScanner',
    'ScanResult',
    'ThreatDetected',
    
    # Middleware components
    'GraphQLPerformanceMiddleware',
    'GraphQLPerformanceView',
    'get_performance_aggregator',
    'setup_performance_monitoring',
    'monitor_performance',
]