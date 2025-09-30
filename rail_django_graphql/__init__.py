"""
Django GraphQL Auto - Génération automatique de schémas GraphQL pour Django.

Ce package fournit des outils pour générer automatiquement des schémas GraphQL
à partir de modèles Django avec des fonctionnalités avancées de sécurité,
de permissions et d'optimisation des performances.
"""

__version__ = "1.0.0"
__author__ = "Django GraphQL Auto Team"
__email__ = "contact@django-graphql-auto.com"

# Configuration par défaut
default_app_config = 'rail_django_graphql.apps.DjangoGraphQLAutoConfig'

# Lazy imports to avoid circular dependencies
def get_type_generator():
    """Get TypeGenerator class with lazy import."""
    from .generators.types import TypeGenerator
    return TypeGenerator

def get_query_generator():
    """Get QueryGenerator class with lazy import."""
    from .generators.queries import QueryGenerator
    return QueryGenerator

def get_mutation_generator():
    """Get MutationGenerator class with lazy import."""
    from .generators.mutations import MutationGenerator
    return MutationGenerator

def get_model_introspector():
    """Get ModelIntrospector class with lazy import."""
    from .generators.introspector import ModelIntrospector
    return ModelIntrospector

# Minimal __all__ to avoid import issues
__all__ = [
    'get_type_generator',
    'get_query_generator', 
    'get_mutation_generator',
    'get_model_introspector',
]