"""
Debug mode enhancements for Django GraphQL Auto-Generation.

This module provides comprehensive debugging tools, detailed error information,
and development utilities for GraphQL schema development and troubleshooting.
"""

import json
import time
import traceback
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from functools import wraps

import graphene
from graphql import GraphQLError
from graphql.execution import ExecutionResult
from graphql.language import print_ast
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from .exceptions import GraphQLAutoError, ErrorCode

logger = logging.getLogger(__name__)


class DebugInfo:
    """Classe pour collecter et formater les informations de débogage."""
    
    def __init__(self):
        self.start_time = time.time()
        self.queries = []
        self.errors = []
        self.performance_data = {}
        self.context_data = {}
    
    def add_query(self, query: str, variables: Dict = None, operation_name: str = None):
        """Ajoute une requête à la liste de débogage."""
        self.queries.append({
            'query': query,
            'variables': variables or {},
            'operation_name': operation_name,
            'timestamp': datetime.now().isoformat(),
        })
    
    def add_error(self, error: Exception, context: Dict = None):
        """Ajoute une erreur à la liste de débogage."""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc() if settings.DEBUG else None,
        }
        
        if context:
            error_info['context'] = context
        
        if isinstance(error, GraphQLAutoError):
            error_info.update({
                'code': error.code.value,
                'field': error.field,
                'details': error.details,
            })
        
        self.errors.append(error_info)
    
    def add_performance_data(self, key: str, value: Any):
        """Ajoute des données de performance."""
        self.performance_data[key] = value
    
    def add_context_data(self, key: str, value: Any):
        """Ajoute des données de contexte."""
        self.context_data[key] = value
    
    def get_execution_time(self) -> float:
        """Retourne le temps d'exécution total."""
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit les informations de débogage en dictionnaire."""
        return {
            'execution_time': self.get_execution_time(),
            'queries': self.queries,
            'errors': self.errors,
            'performance': self.performance_data,
            'context': self.context_data,
            'timestamp': datetime.now().isoformat(),
        }


class GraphQLDebugMiddleware:
    """Middleware de débogage pour GraphQL."""
    
    def __init__(self):
        self.enabled = getattr(settings, 'GRAPHQL_DEBUG', settings.DEBUG)
        self.include_query_ast = getattr(settings, 'GRAPHQL_DEBUG_INCLUDE_AST', False)
        self.include_variables = getattr(settings, 'GRAPHQL_DEBUG_INCLUDE_VARIABLES', True)
        self.include_context = getattr(settings, 'GRAPHQL_DEBUG_INCLUDE_CONTEXT', False)
    
    def process_request(self, request, query, variables=None, operation_name=None):
        """Traite la requête entrante."""
        if not self.enabled:
            return
        
        debug_info = DebugInfo()
        request.graphql_debug = debug_info
        
        # Ajout de la requête
        debug_info.add_query(query, variables, operation_name)
        
        # Ajout des données de contexte
        if self.include_context and hasattr(request, 'user'):
            debug_info.add_context_data('user', {
                'id': getattr(request.user, 'id', None),
                'username': getattr(request.user, 'username', 'anonymous'),
                'is_authenticated': getattr(request.user, 'is_authenticated', False),
            })
        
        debug_info.add_context_data('request_method', request.method)
        debug_info.add_context_data('request_path', request.path)
    
    def process_response(self, request, response):
        """Traite la réponse sortante."""
        if not self.enabled or not hasattr(request, 'graphql_debug'):
            return response
        
        debug_info = request.graphql_debug
        
        # Ajout des informations de débogage à la réponse
        if hasattr(response, 'data') and isinstance(response.data, dict):
            response.data['_debug'] = debug_info.to_dict()
        
        return response
    
    def process_error(self, request, error):
        """Traite les erreurs."""
        if not self.enabled or not hasattr(request, 'graphql_debug'):
            return
        
        debug_info = request.graphql_debug
        debug_info.add_error(error)


class QueryAnalyzer:
    """Analyseur de requêtes GraphQL pour le débogage."""
    
    @staticmethod
    def analyze_query(query_ast) -> Dict[str, Any]:
        """
        Analyse une requête GraphQL et retourne des informations détaillées.
        
        Args:
            query_ast: AST de la requête GraphQL
            
        Returns:
            Dict contenant les informations d'analyse
        """
        analysis = {
            'operations': [],
            'fragments': [],
            'complexity_estimate': 0,
            'depth_estimate': 0,
            'field_count': 0,
        }
        
        if not query_ast or not hasattr(query_ast, 'definitions'):
            return analysis
        
        for definition in query_ast.definitions:
            if hasattr(definition, 'operation'):
                # Opération (query, mutation, subscription)
                operation_info = {
                    'type': definition.operation.value,
                    'name': definition.name.value if definition.name else None,
                    'fields': QueryAnalyzer._extract_fields(definition.selection_set),
                }
                analysis['operations'].append(operation_info)
                
                # Calcul de la complexité et profondeur
                depth = QueryAnalyzer._calculate_depth(definition.selection_set)
                analysis['depth_estimate'] = max(analysis['depth_estimate'], depth)
                
                field_count = QueryAnalyzer._count_fields(definition.selection_set)
                analysis['field_count'] += field_count
                analysis['complexity_estimate'] += field_count
            
            elif hasattr(definition, 'name') and definition.name:
                # Fragment
                fragment_info = {
                    'name': definition.name.value,
                    'type': definition.type_condition.name.value,
                    'fields': QueryAnalyzer._extract_fields(definition.selection_set),
                }
                analysis['fragments'].append(fragment_info)
        
        return analysis
    
    @staticmethod
    def _extract_fields(selection_set, depth=0) -> List[Dict[str, Any]]:
        """Extrait les champs d'un selection set."""
        fields = []
        
        if not selection_set or not hasattr(selection_set, 'selections'):
            return fields
        
        for selection in selection_set.selections:
            if hasattr(selection, 'name'):
                field_info = {
                    'name': selection.name.value,
                    'depth': depth,
                    'arguments': {},
                    'subfields': [],
                }
                
                # Arguments
                if hasattr(selection, 'arguments') and selection.arguments:
                    for arg in selection.arguments:
                        field_info['arguments'][arg.name.value] = str(arg.value.value)
                
                # Sous-champs
                if hasattr(selection, 'selection_set') and selection.selection_set:
                    field_info['subfields'] = QueryAnalyzer._extract_fields(
                        selection.selection_set, depth + 1
                    )
                
                fields.append(field_info)
        
        return fields
    
    @staticmethod
    def _calculate_depth(selection_set, current_depth=1) -> int:
        """Calcule la profondeur maximale d'un selection set."""
        if not selection_set or not hasattr(selection_set, 'selections'):
            return current_depth
        
        max_depth = current_depth
        
        for selection in selection_set.selections:
            if hasattr(selection, 'selection_set') and selection.selection_set:
                depth = QueryAnalyzer._calculate_depth(
                    selection.selection_set, current_depth + 1
                )
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    @staticmethod
    def _count_fields(selection_set) -> int:
        """Compte le nombre total de champs dans un selection set."""
        if not selection_set or not hasattr(selection_set, 'selections'):
            return 0
        
        count = 0
        
        for selection in selection_set.selections:
            count += 1
            if hasattr(selection, 'selection_set') and selection.selection_set:
                count += QueryAnalyzer._count_fields(selection.selection_set)
        
        return count


class PerformanceProfiler:
    """Profileur de performance pour GraphQL."""
    
    def __init__(self):
        self.enabled = getattr(settings, 'GRAPHQL_PERFORMANCE_PROFILING', settings.DEBUG)
        self.profiles = {}
    
    def start_profiling(self, operation_name: str):
        """Démarre le profilage d'une opération."""
        if not self.enabled:
            return
        
        self.profiles[operation_name] = {
            'start_time': time.time(),
            'memory_start': self._get_memory_usage(),
            'db_queries_start': self._get_db_query_count(),
        }
    
    def end_profiling(self, operation_name: str) -> Dict[str, Any]:
        """Termine le profilage et retourne les résultats."""
        if not self.enabled or operation_name not in self.profiles:
            return {}
        
        profile = self.profiles[operation_name]
        end_time = time.time()
        
        result = {
            'execution_time': end_time - profile['start_time'],
            'memory_usage': self._get_memory_usage() - profile['memory_start'],
            'db_queries': self._get_db_query_count() - profile['db_queries_start'],
        }
        
        del self.profiles[operation_name]
        return result
    
    def _get_memory_usage(self) -> int:
        """Retourne l'utilisation mémoire actuelle."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def _get_db_query_count(self) -> int:
        """Retourne le nombre de requêtes DB exécutées."""
        try:
            from django.db import connection
            return len(connection.queries)
        except:
            return 0


class SchemaIntrospector:
    """Introspecteur de schéma pour le débogage."""
    
    @staticmethod
    def get_schema_info(schema) -> Dict[str, Any]:
        """
        Retourne des informations détaillées sur le schéma GraphQL.
        
        Args:
            schema: Schéma GraphQL
            
        Returns:
            Dict contenant les informations du schéma
        """
        info = {
            'types': {},
            'queries': [],
            'mutations': [],
            'subscriptions': [],
            'directives': [],
        }
        
        if not schema or not hasattr(schema, 'type_map'):
            return info
        
        # Types
        for type_name, type_obj in schema.type_map.items():
            if not type_name.startswith('__'):
                info['types'][type_name] = {
                    'kind': str(type_obj),
                    'description': getattr(type_obj, 'description', None),
                }
                
                if hasattr(type_obj, 'fields'):
                    info['types'][type_name]['fields'] = list(type_obj.fields.keys())
        
        # Opérations racine
        if hasattr(schema, 'query_type') and schema.query_type:
            info['queries'] = list(schema.query_type.fields.keys())
        
        if hasattr(schema, 'mutation_type') and schema.mutation_type:
            info['mutations'] = list(schema.mutation_type.fields.keys())
        
        if hasattr(schema, 'subscription_type') and schema.subscription_type:
            info['subscriptions'] = list(schema.subscription_type.fields.keys())
        
        return info


# Instances globales
debug_middleware = GraphQLDebugMiddleware()
performance_profiler = PerformanceProfiler()


def debug_resolver(resolver_func):
    """
    Décorateur pour ajouter des informations de débogage aux résolveurs.
    
    Args:
        resolver_func: Fonction de résolution à décorer
        
    Returns:
        Fonction décorée avec débogage
    """
    @wraps(resolver_func)
    def wrapper(root, info, **kwargs):
        if not getattr(settings, 'GRAPHQL_DEBUG', settings.DEBUG):
            return resolver_func(root, info, **kwargs)
        
        field_name = info.field_name
        start_time = time.time()
        
        try:
            result = resolver_func(root, info, **kwargs)
            
            # Log du succès
            execution_time = time.time() - start_time
            logger.debug(
                f"Resolver '{field_name}' executed successfully in {execution_time:.3f}s",
                extra={
                    'field_name': field_name,
                    'execution_time': execution_time,
                    'args': kwargs,
                }
            )
            
            return result
            
        except Exception as e:
            # Log de l'erreur avec contexte
            execution_time = time.time() - start_time
            logger.error(
                f"Resolver '{field_name}' failed after {execution_time:.3f}s: {str(e)}",
                extra={
                    'field_name': field_name,
                    'execution_time': execution_time,
                    'args': kwargs,
                    'error': str(e),
                },
                exc_info=True
            )
            
            raise
    
    return wrapper


class DebugQuery(graphene.ObjectType):
    """Requêtes de débogage pour GraphQL."""
    
    schema_info = graphene.Field(
        graphene.JSONString,
        description="Informations sur le schéma GraphQL"
    )
    
    query_analysis = graphene.Field(
        graphene.JSONString,
        query=graphene.String(required=True),
        description="Analyse d'une requête GraphQL"
    )
    
    def resolve_schema_info(self, info):
        """Retourne les informations du schéma."""
        if not getattr(settings, 'GRAPHQL_DEBUG', settings.DEBUG):
            raise GraphQLAutoError(
                "Les informations de débogage ne sont disponibles qu'en mode debug",
                code=ErrorCode.FEATURE_DISABLED
            )
        
        return SchemaIntrospector.get_schema_info(info.schema)
    
    def resolve_query_analysis(self, info, query: str):
        """Analyse une requête GraphQL."""
        if not getattr(settings, 'GRAPHQL_DEBUG', settings.DEBUG):
            raise GraphQLAutoError(
                "L'analyse de requête n'est disponible qu'en mode debug",
                code=ErrorCode.FEATURE_DISABLED
            )
        
        try:
            from graphql import parse
            query_ast = parse(query)
            return QueryAnalyzer.analyze_query(query_ast)
        except Exception as e:
            raise GraphQLAutoError(
                f"Erreur lors de l'analyse de la requête: {str(e)}",
                code=ErrorCode.VALIDATION_ERROR,
                original_error=e
            )