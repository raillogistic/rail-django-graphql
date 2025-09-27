"""
Query Generation System for Django GraphQL Auto-Generation

This module provides the QueryGenerator class, which is responsible for creating
GraphQL queries for Django models, including single object, list, and filtered queries.
"""

from typing import Any, Dict, List, Optional, Type, Union

import graphene
from django.db import models
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from ..core.settings import QueryGeneratorSettings
from .types import TypeGenerator
from .filters import AdvancedFilterGenerator
from ..extensions.optimization import (
    get_optimizer, 
    get_performance_monitor, 
    optimize_query,
    QueryOptimizationConfig
)


class PaginationInfo(graphene.ObjectType):
    """
    Informations de pagination pour les requêtes GraphQL paginées.
    
    Cette classe est définie au niveau du module pour permettre la sérialisation
    (pickle) lors de la mise en cache des résultats.
    """
    total_count = graphene.Int(description="Total number of records")
    page_count = graphene.Int(description="Total number of pages")
    current_page = graphene.Int(description="Current page number")
    per_page = graphene.Int(description="Number of records per page")
    has_next_page = graphene.Boolean(description="Whether there is a next page")
    has_previous_page = graphene.Boolean(description="Whether there is a previous page")


class PaginatedResult:
    """
    Classe de résultat paginé pour les requêtes GraphQL.
    
    Cette classe est définie au niveau du module pour permettre la sérialisation
    (pickle) lors de la mise en cache des résultats.
    """
    def __init__(self, items, page_info):
        self.items = items
        self.page_info = page_info

class QueryGenerator:
    """
    Creates GraphQL queries for Django models, supporting single object lookups,
    list queries, filtering, and pagination.
    """

    def __init__(self, type_generator: TypeGenerator, settings: Optional[QueryGeneratorSettings] = None):
        self.type_generator = type_generator
        self.settings = settings or QueryGeneratorSettings()
        self.filter_generator = AdvancedFilterGenerator()
        self._query_fields: Dict[str, graphene.Field] = {}
        
        # Initialize performance optimization
        self.optimizer = get_optimizer()
        self.performance_monitor = get_performance_monitor()

    def generate_single_query(self, model: Type[models.Model]) -> graphene.Field:
        """
        Generates a query field for retrieving a single model instance.
        Supports lookup by ID and other unique fields.
        """
        model_type = self.type_generator.generate_object_type(model)
        model_name = model.__name__.lower()

        @optimize_query()
        def resolver(root: Any, info: graphene.ResolveInfo, **kwargs) -> Optional[models.Model]:
            try:
                # If no arguments provided, return None instead of trying to get all records
                if not kwargs:
                    return None
                    
                filters = Q()
                for key, value in kwargs.items():
                    filters |= Q(**{key: value})
                
                # Get optimized queryset
                queryset = model.objects.all()
                queryset = self.optimizer.optimize_queryset(queryset, info, model)
                
                return queryset.get(filters)
            except model.DoesNotExist:
                return None

        # Define arguments for the query
        arguments = {
            'id': graphene.ID(description=f"The ID of the {model_name} to retrieve"),
        }

        # Add additional lookup fields from settings
        for field_name in self.settings.additional_lookup_fields.get(model.__name__, []):
            field = model._meta.get_field(field_name)
            graphql_type = self.type_generator.FIELD_TYPE_MAP.get(type(field), graphene.String)
            arguments[field_name] = graphql_type(description=f"Look up {model_name} by {field_name}")

        return graphene.Field(
            model_type,
            args=arguments,
            resolver=resolver,
            description=f"Retrieve a single {model_name} instance"
        )

    def generate_list_query(self, model: Type[models.Model]) -> Union[graphene.List, DjangoFilterConnectionField]:
        """
        Generates a query field for retrieving a list of model instances.
        Supports advanced filtering, pagination, and ordering.
        """
        model_type = self.type_generator.generate_object_type(model)
        model_name = model.__name__.lower()
        filter_class = self.filter_generator.generate_filter_set(model)
        complex_filter_input = self.filter_generator.generate_complex_filter_input(model)

        if self.settings.use_relay:
            # Use Relay connection for cursor-based pagination
            return DjangoFilterConnectionField(
                model_type,
                filterset_class=filter_class,
                description=f"Retrieve a list of {model_name} instances with pagination"
            )
        else:
            @optimize_query()
            def resolver(root: Any, info: graphene.ResolveInfo, **kwargs) -> List[models.Model]:
                queryset = model.objects.all()
                
                # Apply query optimization first
                queryset = self.optimizer.optimize_queryset(queryset, info, model)

                # Apply advanced filtering
                filters = kwargs.get('filters')
                if filters:
                    queryset = self.filter_generator.apply_complex_filters(queryset, filters)

                # Apply basic filtering
                basic_filters = {k: v for k, v in kwargs.items() if k not in ['filters', 'order_by', 'page', 'per_page']}
                if basic_filters and filter_class:
                    filterset = filter_class(basic_filters, queryset)
                    queryset = filterset.qs

                # Apply ordering
                order_by = kwargs.get('order_by')
                if order_by:
                    queryset = queryset.order_by(*order_by)

                # Apply pagination
                offset = kwargs.get('offset')
                limit = kwargs.get('limit')
                if offset is not None and limit is not None:
                    queryset = queryset[offset:offset + limit]
                elif limit is not None:
                    queryset = queryset[:limit]

                return queryset

            # Define arguments for the query
            arguments = {}

            # Add complex filtering argument
            arguments['filters'] = graphene.Argument(
                complex_filter_input,
                description="Advanced filtering with AND, OR, NOT operations"
            )

            # Add basic filtering arguments if filter class is available
            if filter_class:
                for name, field in filter_class.base_filters.items():
                    field_type = graphene.String  # Default to String
                    
                    # Map filter types to GraphQL types
                    if hasattr(field, 'field_class'):
                        if 'Number' in field.__class__.__name__ or 'Integer' in field.__class__.__name__:
                            field_type = graphene.Float
                        elif 'Boolean' in field.__class__.__name__:
                            field_type = graphene.Boolean
                        elif 'Date' in field.__class__.__name__:
                            field_type = graphene.Date
                    
                    # Handle ModelMultipleChoiceFilter for __in filters
                    if 'ModelMultipleChoiceFilter' in field.__class__.__name__ or name.endswith('__in'):
                        # For __in filters, use List of appropriate type
                        if 'Number' in field.__class__.__name__ or 'Integer' in field.__class__.__name__:
                            field_type = graphene.List(graphene.Float)
                        else:
                            field_type = graphene.List(graphene.String)
                    
                    arguments[name] = graphene.Argument(
                        field_type,
                        description=getattr(field, 'help_text', f'Filter by {name}')
                    )

            # Add pagination arguments
            if self.settings.enable_pagination:
                arguments.update({
                    'offset': graphene.Int(description="Number of records to skip"),
                    'limit': graphene.Int(description="Number of records to return")
                })

            # Add ordering arguments
            if self.settings.enable_ordering:
                arguments['order_by'] = graphene.List(
                    graphene.String,
                    description="Fields to order by (prefix with - for descending)"
                )

            return graphene.List(
                model_type,
                args=arguments,
                resolver=resolver,
                description=f"Retrieve a list of {model_name} instances"
            )

    def generate_paginated_query(self, model: Type[models.Model]) -> graphene.Field:
        """
        Generates a query field with advanced pagination support.
        Returns both the paginated results and pagination metadata.
        """
        model_type = self.type_generator.generate_object_type(model)
        model_name = model.__name__.lower()

        # Create a pagination info type (using module-level class)
        # PaginationInfo is now defined at module level for pickle support

        # Create a model-specific connection type for the paginated results
        connection_name = f"{model.__name__}PaginatedConnection"
        PaginatedConnection = type(connection_name, (graphene.ObjectType,), {
            'items': graphene.List(model_type, description=f"List of {model_name} instances"),
            'page_info': graphene.Field(PaginationInfo, description="Pagination metadata")
        })

        @optimize_query()
        def resolver(root: Any, info: graphene.ResolveInfo, **kwargs) -> PaginatedConnection:
            queryset = model.objects.all()
            
            # Apply query optimization first
            queryset = self.optimizer.optimize_queryset(queryset, info, model)
            
            # Apply advanced filtering (same as list queries)
            filters = kwargs.get('filters')
            if filters:
                queryset = self.filter_generator.apply_complex_filters(queryset, filters)

            # Apply basic filtering (same as list queries)
            basic_filters = {k: v for k, v in kwargs.items() if k not in ['filters', 'order_by', 'page', 'per_page']}
            filter_class = self.filter_generator.generate_filter_set(model)
            if basic_filters and filter_class:
                filterset = filter_class(basic_filters, queryset)
                if filterset.is_valid():
                    queryset = filterset.qs
                else:
                    # If filterset is invalid, return empty result
                    class EmptyPaginationInfo:
                        def __init__(self):
                            self.total_count = 0
                            self.page_count = 0
                            self.current_page = 1
                            self.per_page = per_page
                            self.has_next_page = False
                            self.has_previous_page = False
                    
                    class EmptyPaginatedResult:
                        def __init__(self):
                            self.items = []
                            self.page_info = EmptyPaginationInfo()
                    
                    return EmptyPaginatedResult()

            # Apply ordering (same as list queries)
            order_by = kwargs.get('order_by')
            if order_by:
                queryset = queryset.order_by(*order_by)

            # Calculate pagination values
            page = kwargs.get('page', 1)
            per_page = kwargs.get('per_page', self.settings.default_page_size)
            total_count = queryset.count()
            page_count = (total_count + per_page - 1) // per_page

            # Ensure page is within valid range
            page = max(1, min(page, page_count))

            # Apply pagination
            start = (page - 1) * per_page
            end = start + per_page
            items = queryset[start:end]

            # Create pagination info
            page_info = PaginationInfo(
                total_count=total_count,
                page_count=page_count,
                current_page=page,
                per_page=per_page,
                has_next_page=page < page_count,
                has_previous_page=page > 1
            )

            # Return a simple object with the required attributes
            return PaginatedResult(items=items, page_info=page_info)

        # Define arguments for the query
        arguments = {
            'page': graphene.Int(description="Page number (1-based)", default_value=1),
            'per_page': graphene.Int(
                description="Number of records per page",
                default_value=self.settings.default_page_size
            )
        }

        # Add complex filtering argument (same as list queries)
        filter_class = self.filter_generator.generate_filter_set(model)
        complex_filter_input = self.filter_generator.generate_complex_filter_input(model)
        
        arguments['filters'] = graphene.Argument(
            complex_filter_input,
            description="Advanced filtering with AND, OR, NOT operations"
        )

        # Add basic filtering arguments if filter class is available (same as list queries)
        if filter_class:
            for name, field in filter_class.base_filters.items():
                field_type = graphene.String  # Default to String
                
                # Map filter types to GraphQL types (same logic as list queries)
                if hasattr(field, 'field_class'):
                    if 'Number' in field.__class__.__name__ or 'Integer' in field.__class__.__name__:
                        field_type = graphene.Float
                    elif 'Boolean' in field.__class__.__name__:
                        field_type = graphene.Boolean
                    elif 'Date' in field.__class__.__name__:
                        field_type = graphene.Date
                
                # Handle ModelMultipleChoiceFilter for __in filters
                if 'ModelMultipleChoiceFilter' in field.__class__.__name__ or name.endswith('__in'):
                    # For __in filters, use List of appropriate type
                    if 'Number' in field.__class__.__name__ or 'Integer' in field.__class__.__name__:
                        field_type = graphene.List(graphene.Float)
                    else:
                        field_type = graphene.List(graphene.String)
                
                arguments[name] = graphene.Argument(
                    field_type,
                    description=getattr(field, 'help_text', f'Filter by {name}')
                )

        # Add ordering arguments (same as list queries)
        if self.settings.enable_ordering:
            arguments['order_by'] = graphene.List(
                graphene.String,
                description="Fields to order by (prefix with - for descending)"
            )

        return graphene.Field(
            PaginatedConnection,
            args=arguments,
            resolver=resolver,
            description=f"Retrieve a paginated list of {model_name} instances"
        )

    def add_filtering_support(self, query: graphene.Field, model: Type[models.Model]) -> graphene.Field:
        """
        Adds filtering capabilities to an existing query field.
        """
        filter_class = self.type_generator.generate_filter_type(model)
        if not filter_class:
            return query

        # Add filter arguments to the query
        for name, field in filter_class.base_filters.items():
            query.args[name] = graphene.Argument(
                self.type_generator.FIELD_TYPE_MAP.get(type(field), graphene.String)
            )

        # Wrap the original resolver to apply filters
        original_resolver = query.resolver
        def filtered_resolver(root: Any, info: graphene.ResolveInfo, **kwargs):
            result = original_resolver(root, info, **kwargs)
            if isinstance(result, models.QuerySet):
                filterset = filter_class(kwargs, result)
                return filterset.qs
            return result

        query.resolver = filtered_resolver
        return query