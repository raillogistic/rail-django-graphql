"""
Django GraphQL Auto - Génération automatique de schémas GraphQL pour Django.

Ce package fournit des outils pour générer automatiquement des schémas GraphQL
à partir de modèles Django avec des fonctionnalités avancées de sécurité,
de permissions et d'optimisation des performances.
"""

__version__ = "1.0.0"
__author__ = "Django GraphQL Auto Team"
__email__ = "contact@django-graphql-auto.com"

# Imports principaux disponibles
from .generators.types import TypeGenerator
from .generators.queries import QueryGenerator
from .generators.mutations import MutationGenerator
from .generators.introspector import ModelIntrospector

# Imports d'optimisation des performances disponibles
from .extensions.optimization import (
    QueryOptimizer,
    QueryAnalyzer,
    PerformanceMonitor
)
from .extensions.caching import (
    GraphQLCacheManager
)

# Imports de gestion des fichiers et médias disponibles
from .generators.file_uploads import (
    FileUploadGenerator
)
from .extensions.media import (
    MediaManager
)

# Configuration par défaut
default_app_config = 'django_graphql_auto.apps.DjangoGraphQLAutoConfig'

__all__ = [
    # Core components disponibles
    'TypeGenerator',
    'QueryGenerator',
    'MutationGenerator',
    'ModelIntrospector',
    
    # Performance optimization components disponibles
    'QueryOptimizer',
    'QueryAnalyzer',
    'PerformanceMonitor',
    
    # Caching components disponibles
    'GraphQLCacheManager',
    
    # File upload and media components disponibles
    'FileUploadGenerator',
    'MediaManager',
]