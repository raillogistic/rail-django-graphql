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

class QueryGenerator:
    """
    Creates GraphQL queries for Django models, supporting single object lookups,
    list queries, filtering, and pagination.
    """

    def __init__(self, type_generator: TypeGenerator, settings: Optional[QueryGeneratorSettings] = None):
        self.type_generator = type_generator
        self.settings = settings or QueryGeneratorSettings()
        self._query_fields: Dict[str, graphene.Field] = {}

    def generate_single_query(self, model: Type[models.Model]) -> graphene.Field:
        """
        Generates a query field for retrieving a single model instance.
        Supports lookup by ID and other unique fields.
        """
        model_type = self.type_generator.generate_object_type(model)
        model_name = model.__name__.lower()

        def resolver(root: Any, info: graphene.ResolveInfo, **kwargs) -> Optional[models.Model]:
            try:
                filters = Q()
                for key, value in kwargs.items():
                    filters |= Q(**{key: value})
                return model.objects.get(filters)
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
        Supports filtering, pagination, and ordering.
        """
        model_type = self.type_generator.generate_object_type(model)
        model_name = model.__name__.lower()
        filter_class = self.type_generator.generate_filter_type(model)

        if self.settings.use_relay:
            # Use Relay connection for cursor-based pagination
            return DjangoFilterConnectionField(
                model_type,
                filterset_class=filter_class,
                description=f"Retrieve a list of {model_name} instances with pagination"
            )
        else:
            def resolver(root: Any, info: graphene.ResolveInfo, **kwargs) -> List[models.Model]:
                queryset = model.objects.all()

                # Apply filtering
                if filter_class and kwargs:
                    filterset = filter_class(kwargs, queryset=queryset)
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

            # Add filtering arguments if filter class is available
            if filter_class:
                for name, field in filter_class.base_filters.items():
                    arguments[name] = graphene.Argument(
                        self.type_generator.FIELD_TYPE_MAP.get(
                            type(field), graphene.String
                        )
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

        # Create a pagination info type
        class PaginationInfo(graphene.ObjectType):
            total_count = graphene.Int(description="Total number of records")
            page_count = graphene.Int(description="Total number of pages")
            current_page = graphene.Int(description="Current page number")
            per_page = graphene.Int(description="Number of records per page")
            has_next_page = graphene.Boolean(description="Whether there is a next page")
            has_previous_page = graphene.Boolean(description="Whether there is a previous page")

        # Create a connection type for the paginated results
        class PaginatedConnection(graphene.ObjectType):
            items = graphene.List(model_type, description=f"List of {model_name} instances")
            page_info = graphene.Field(PaginationInfo, description="Pagination metadata")

        def resolver(root: Any, info: graphene.ResolveInfo, **kwargs) -> PaginatedConnection:
            queryset = model.objects.all()
            
            # Apply filtering
            filter_class = self.type_generator.generate_filter_type(model)
            if filter_class and kwargs:
                filterset = filter_class(kwargs, queryset=queryset)
                queryset = filterset.qs

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

            return PaginatedConnection(items=items, page_info=page_info)

        # Define arguments for the query
        arguments = {
            'page': graphene.Int(description="Page number (1-based)", default_value=1),
            'per_page': graphene.Int(
                description="Number of records per page",
                default_value=self.settings.default_page_size
            )
        }

        # Add filter arguments if available
        filter_class = self.type_generator.generate_filter_type(model)
        if filter_class:
            for name, field in filter_class.base_filters.items():
                arguments[name] = graphene.Argument(
                    self.type_generator.FIELD_TYPE_MAP.get(type(field), graphene.String)
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
                filterset = filter_class(kwargs, queryset=result)
                return filterset.qs
            return result

        query.resolver = filtered_resolver
        return query