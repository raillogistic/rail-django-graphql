"""
Advanced Filtering System for Django GraphQL Auto-Generation

This module provides the FilterGenerator class, which creates sophisticated
GraphQL filters based on Django model field types, supporting complex
filter combinations and field-specific operations.
"""

from typing import Any, Dict, List, Optional, Type, Union, Set
import graphene
from django.db import models
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
import django_filters
from django_filters import FilterSet, CharFilter, NumberFilter, DateFilter, BooleanFilter, ChoiceFilter
import logging

from .introspector import ModelIntrospector

logger = logging.getLogger(__name__)

# Configuration constants for nested filtering
DEFAULT_MAX_NESTED_DEPTH = 3
MAX_ALLOWED_NESTED_DEPTH = 5


class AdvancedFilterGenerator:
    """
    Generates advanced GraphQL filters for Django models based on field types.
    
    This class creates sophisticated filtering capabilities for GraphQL queries,
    supporting various field types and operations including text search, numeric
    ranges, date filtering, boolean logic, and nested relationship filtering.
    
    Features:
    - Field-specific filter operations (contains, exact, range, etc.)
    - Nested relationship filtering with configurable depth
    - Complex logical combinations (AND, OR, NOT)
    - Caching for performance optimization
    - Multi-schema support for different filtering configurations
    
    Supported Field Types:
    - CharField: contains, icontains, exact, iexact, startswith, endswith
    - IntegerField/FloatField: exact, lt, lte, gt, gte, range
    - DateField/DateTimeField: exact, lt, lte, gt, gte, range, year, month, day
    - BooleanField: exact
    - ChoiceField: exact, in
    - ForeignKey/OneToOne: nested filtering on related model fields
    - ManyToMany: nested filtering with multiple related objects
    
    Args:
        max_nested_depth: Maximum depth for nested relationship filtering (default: 3, max: 5)
        enable_nested_filters: Whether to enable nested field filtering (default: True)
        schema_name: Optional schema name for context (for future multi-schema support)
    
    Example:
        >>> filter_generator = AdvancedFilterGenerator(max_nested_depth=2)
        >>> filter_class = filter_generator.generate_filter_class(User)
        >>> # Creates filters like: name__contains, email__iexact, profile__bio__contains
    """

    def __init__(self, max_nested_depth: int = DEFAULT_MAX_NESTED_DEPTH, 
                 enable_nested_filters: bool = True, schema_name: Optional[str] = None):
        """
        Initialize the filter generator with nested filtering configuration.
        
        Args:
            max_nested_depth: Maximum depth for nested relationship filtering (default: 3, max: 5)
            enable_nested_filters: Whether to enable nested field filtering (default: True)
            schema_name: Optional schema name for context (for future multi-schema support)
        """
        self._filter_cache: Dict[Type[models.Model], Type[FilterSet]] = {}
        self.max_nested_depth = min(max_nested_depth, MAX_ALLOWED_NESTED_DEPTH)
        self.enable_nested_filters = enable_nested_filters
        self.schema_name = schema_name or 'default'
        self._visited_models: set = set()  # Track visited models to prevent infinite recursion
        
        # Log configuration for debugging
        logger.debug(
            f"Initialized AdvancedFilterGenerator for schema '{self.schema_name}' "
            f"with max_nested_depth={self.max_nested_depth}, "
            f"enable_nested_filters={self.enable_nested_filters}"
        )

    def generate_filter_set(self, model: Type[models.Model], current_depth: int = 0) -> Type[FilterSet]:
        """
        Generate a FilterSet class for the given Django model with nested filtering support.
        
        Args:
            model: Django model to generate filters for
            current_depth: Current nesting depth (used for recursion control)
            
        Returns:
            FilterSet class with comprehensive filtering capabilities
        """
        # Create cache key based on model and depth
        cache_key = f"{model.__name__}_{current_depth}"
        
        if cache_key in self._filter_cache:
            logger.debug(f"Returning cached FilterSet for {cache_key}")
            return self._filter_cache[cache_key]
        
        # Prevent infinite recursion
        if model in self._visited_models:
            logger.warning(f"Circular reference detected for model {model.__name__} at depth {current_depth}")
            return self._generate_basic_filter_set(model)
        
        # Check depth limits
        if current_depth >= self.max_nested_depth:
            logger.debug(f"Maximum nested depth ({self.max_nested_depth}) reached for {model.__name__}")
            return self._generate_basic_filter_set(model)
        
        # Add model to visited set
        self._visited_models.add(model)
        
        try:
            # Generate filters for all fields
            filters = {}
            for field in model._meta.get_fields():
                if hasattr(field, 'name'):  # Skip reverse relations without names
                    field_filters = self._generate_field_filters(field, current_depth, allow_nested=True)
                    filters.update(field_filters)
            
            # Generate reverse relationship count filters
            reverse_count_filters = self._generate_reverse_relationship_count_filters(model)
            filters.update(reverse_count_filters)
            
            # Generate property filters
            property_filters = self._generate_property_filters(model)
            filters.update(property_filters)
            
            # Generate dynamic filter methods for count filters
            filter_methods = self._generate_count_filter_methods(model, filters)
            
            # Create FilterSet class
            filter_set_class = type(
                f'{model.__name__}FilterSet',
                (FilterSet,),
                {
                    **filters,
                    **filter_methods,
                    'Meta': type('Meta', (), {
                        'model': model,
                        'fields': list(filters.keys()),
                        'strict': False,  # Allow partial matches
                    })
                }
            )
            
            # Cache the result
            self._filter_cache[cache_key] = filter_set_class
            logger.debug(f"Generated FilterSet for {model.__name__} with {len(filters)} filters at depth {current_depth}")
            
            return filter_set_class
            
        finally:
            # Remove model from visited set to allow it in other branches
            self._visited_models.discard(model)

    def _generate_basic_filter_set(self, model: Type[models.Model]) -> Type[FilterSet]:
        """
        Create a basic FilterSet without nested relationships to prevent infinite recursion.
        
        Args:
            model: Django model to generate basic filters for
            
        Returns:
            Basic FilterSet class without nested filtering
        """
        cache_key = f"{model.__name__}_basic"
        
        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]
        
        # Generate only basic field filters (no nested relationships)
        filters = {}
        for field in model._meta.get_fields():
            if hasattr(field, 'name'):  # Skip reverse relations without names
                field_filters = self._generate_field_filters(field, 0, allow_nested=False)
                filters.update(field_filters)
        
        filter_set_class = type(
            f'{model.__name__}BasicFilterSet',
            (FilterSet,),
            {
                **filters,
                'Meta': type('Meta', (), {
                    'model': model,
                    'fields': list(filters.keys()),
                    'strict': False,
                })
            }
        )
        
        self._filter_cache[cache_key] = filter_set_class
        logger.debug(f"Generated basic FilterSet for {model.__name__} with {len(filters)} filters")
        
        return filter_set_class

    def _generate_field_filters(self, field: models.Field, current_depth: int = 0, allow_nested: bool = True) -> Dict[str, django_filters.Filter]:
        """
        Generates specific filters based on Django field type.
        
        Args:
            field: Django model field
            current_depth: Current nesting depth for recursive calls
            allow_nested: Whether to allow nested field generation
            
        Returns:
            Dictionary of filter name to Filter instance mappings
        """
        filters = {}
        field_name = field.name

        if isinstance(field, (models.CharField, models.TextField)):
            filters.update(self._generate_text_filters(field_name))
        elif isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
            filters.update(self._generate_numeric_filters(field_name))
        elif isinstance(field, (models.DateField, models.DateTimeField)):
            filters.update(self._generate_date_filters(field_name))
        elif isinstance(field, models.BooleanField):
            filters.update(self._generate_boolean_filters(field_name))
        elif isinstance(field, (models.FileField, models.ImageField)):
            filters.update(self._generate_file_filters(field_name))
        elif isinstance(field, models.JSONField):
            filters.update(self._generate_json_filters(field_name))
        elif hasattr(field, 'choices') and field.choices:
            filters.update(self._generate_choice_filters(field_name, field.choices))
        elif isinstance(field, models.ForeignKey):
            # Only generate basic foreign key filters if nested filtering is enabled
            if self.enable_nested_filters:
                filters.update(self._generate_foreign_key_filters(field_name, field.related_model))
            
            # Add nested field filters if enabled and within depth limits
            if (self.enable_nested_filters and allow_nested and 
                current_depth < self.max_nested_depth and 
                field.related_model not in self._visited_models):
                filters.update(self._generate_nested_field_filters(field, current_depth))
        elif isinstance(field, models.ManyToManyField):
            # Generate ManyToMany filters
            if self.enable_nested_filters:
                filters.update(self._generate_many_to_many_filters(field_name, field.related_model))
            
            # Add nested field filters if enabled and within depth limits
            if (self.enable_nested_filters and allow_nested and 
                current_depth < self.max_nested_depth and 
                field.related_model not in self._visited_models):
                filters.update(self._generate_nested_field_filters(field, current_depth))

        return filters

    def _generate_count_filter_methods(self, model: Type[models.Model], filters: Dict[str, django_filters.Filter]) -> Dict[str, callable]:
        """
        Generate dynamic filter methods for count-based filtering.
        
        Args:
            model: Django model
            filters: Dictionary of filters that have been generated
            
        Returns:
            Dictionary of method names to method implementations
        """
        methods = {}
        
        # Generate methods for ManyToMany count filters
        for field in model._meta.get_fields():
            if isinstance(field, models.ManyToManyField):
                field_name = field.name
                
                # Generate count filter methods
                methods[f'filter_{field_name}_count'] = self._create_count_filter_method(field_name, 'exact')
                methods[f'filter_{field_name}_count_gt'] = self._create_count_filter_method(field_name, 'gt')
                methods[f'filter_{field_name}_count_gte'] = self._create_count_filter_method(field_name, 'gte')
                methods[f'filter_{field_name}_count_lt'] = self._create_count_filter_method(field_name, 'lt')
                methods[f'filter_{field_name}_count_lte'] = self._create_count_filter_method(field_name, 'lte')
        
        # Generate methods for reverse ManyToOne count filters
        if hasattr(model._meta, 'related_objects'):
            for rel in model._meta.related_objects:
                # Skip OneToOne reverse relationships
                from django.db.models.fields.reverse_related import OneToOneRel
                if isinstance(rel, OneToOneRel):
                    continue
                
                accessor_name = rel.get_accessor_name()
                if accessor_name:
                    methods[f'filter_{accessor_name}_count'] = self._create_reverse_count_filter_method(accessor_name, 'exact')
                    methods[f'filter_{accessor_name}_count_gt'] = self._create_reverse_count_filter_method(accessor_name, 'gt')
                    methods[f'filter_{accessor_name}_count_gte'] = self._create_reverse_count_filter_method(accessor_name, 'gte')
                    methods[f'filter_{accessor_name}_count_lt'] = self._create_reverse_count_filter_method(accessor_name, 'lt')
                    methods[f'filter_{accessor_name}_count_lte'] = self._create_reverse_count_filter_method(accessor_name, 'lte')
        
        return methods

    def _create_count_filter_method(self, field_name: str, lookup_type: str):
        """
        Create a filter method for ManyToMany count filtering.
        
        Args:
            field_name: Name of the ManyToMany field
            lookup_type: Type of lookup (exact, gt, gte, lt, lte)
            
        Returns:
            Filter method function
        """
        def filter_method(self, queryset, name, value):
            if value is None:
                return queryset
            
            from django.db.models import Count
            
            # Annotate with count and filter
            count_field = f'{field_name}_count_annotation'
            queryset = queryset.annotate(**{count_field: Count(field_name)})
            
            if lookup_type == 'exact':
                return queryset.filter(**{count_field: value})
            elif lookup_type == 'gt':
                return queryset.filter(**{f'{count_field}__gt': value})
            elif lookup_type == 'gte':
                return queryset.filter(**{f'{count_field}__gte': value})
            elif lookup_type == 'lt':
                return queryset.filter(**{f'{count_field}__lt': value})
            elif lookup_type == 'lte':
                return queryset.filter(**{f'{count_field}__lte': value})
            
            return queryset
        
        return filter_method

    def _create_reverse_count_filter_method(self, accessor_name: str, lookup_type: str):
        """
        Create a filter method for reverse ManyToOne count filtering.
        
        Args:
            accessor_name: Name of the reverse relationship accessor
            lookup_type: Type of lookup (exact, gt, gte, lt, lte)
            
        Returns:
            Filter method function
        """
        def filter_method(self, queryset, name, value):
            if value is None:
                return queryset
            
            from django.db.models import Count
            
            # Annotate with count and filter
            count_field = f'{accessor_name}_count_annotation'
            queryset = queryset.annotate(**{count_field: Count(accessor_name)})
            
            if lookup_type == 'exact':
                return queryset.filter(**{count_field: value})
            elif lookup_type == 'gt':
                return queryset.filter(**{f'{count_field}__gt': value})
            elif lookup_type == 'gte':
                return queryset.filter(**{f'{count_field}__gte': value})
            elif lookup_type == 'lt':
                return queryset.filter(**{f'{count_field}__lt': value})
            elif lookup_type == 'lte':
                return queryset.filter(**{f'{count_field}__lte': value})
            
            return queryset
        
        return filter_method

    def _generate_reverse_relationship_count_filters(self, model: Type[models.Model]) -> Dict[str, django_filters.Filter]:
        """
        Generate count filters for reverse ManyToOne relationships.
        
        Args:
            model: Django model to generate reverse relationship count filters for
            
        Returns:
            Dictionary of filter name to Filter instance mappings
        """
        filters = {}
        
        # Get reverse relationships from model meta
        if hasattr(model._meta, 'related_objects'):
            for rel in model._meta.related_objects:
                # Skip OneToOne reverse relationships as they don't need count filters
                from django.db.models.fields.reverse_related import OneToOneRel
                if isinstance(rel, OneToOneRel):
                    continue
                
                accessor_name = rel.get_accessor_name()
                if accessor_name:
                    # Add count filters for reverse ManyToOne relationships
                    filters[f'{accessor_name}_count'] = NumberFilter(
                        method=f'filter_{accessor_name}_count',
                        help_text=f'Filter by count of {accessor_name} relationships'
                    )
                    filters[f'{accessor_name}_count__gt'] = NumberFilter(
                        method=f'filter_{accessor_name}_count_gt',
                        help_text=f'Filter by count of {accessor_name} relationships greater than'
                    )
                    filters[f'{accessor_name}_count__gte'] = NumberFilter(
                        method=f'filter_{accessor_name}_count_gte',
                        help_text=f'Filter by count of {accessor_name} relationships greater than or equal'
                    )
                    filters[f'{accessor_name}_count__lt'] = NumberFilter(
                        method=f'filter_{accessor_name}_count_lt',
                        help_text=f'Filter by count of {accessor_name} relationships less than'
                    )
                    filters[f'{accessor_name}_count__lte'] = NumberFilter(
                        method=f'filter_{accessor_name}_count_lte',
                        help_text=f'Filter by count of {accessor_name} relationships less than or equal'
                    )
        
        return filters

    def _create_property_filter_method(self, property_name: str, lookup_expr: str):
        """
        Create a custom filter method for property-based filtering.
        
        Args:
            property_name: Name of the property to filter on
            lookup_expr: Django lookup expression (e.g., 'exact', 'icontains', 'gt')
            
        Returns:
            Filter method that can be used with django-filter
        """
        def filter_method(queryset, name, value):
            """
            Custom filter method for property-based filtering.
            
            Since properties are computed at runtime, we need to evaluate
            them for each object and filter accordingly.
            """
            if value is None:
                return queryset
            
            # Get all objects and evaluate the property
            filtered_ids = []
            
            for obj in queryset:
                try:
                    # Get the property value
                    property_value = getattr(obj, property_name)
                    
                    # Apply the lookup expression
                    if self._property_matches_filter(property_value, value, lookup_expr):
                        filtered_ids.append(obj.pk)
                        
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error evaluating property {property_name} on {obj}: {e}")
                    continue
            
            # Return filtered queryset
            return queryset.filter(pk__in=filtered_ids)
        
        return filter_method

    def _property_matches_filter(self, property_value: Any, filter_value: Any, lookup_expr: str) -> bool:
        """
        Check if a property value matches the filter criteria.
        
        Args:
            property_value: The actual value of the property
            filter_value: The value to filter by
            lookup_expr: The lookup expression to apply
            
        Returns:
            True if the property value matches the filter criteria
        """
        try:
            if lookup_expr == 'exact':
                return property_value == filter_value
            elif lookup_expr == 'iexact':
                return str(property_value).lower() == str(filter_value).lower()
            elif lookup_expr == 'contains':
                return str(filter_value) in str(property_value)
            elif lookup_expr == 'icontains':
                return str(filter_value).lower() in str(property_value).lower()
            elif lookup_expr == 'startswith':
                return str(property_value).startswith(str(filter_value))
            elif lookup_expr == 'istartswith':
                return str(property_value).lower().startswith(str(filter_value).lower())
            elif lookup_expr == 'endswith':
                return str(property_value).endswith(str(filter_value))
            elif lookup_expr == 'iendswith':
                return str(property_value).lower().endswith(str(filter_value).lower())
            elif lookup_expr == 'gt':
                return property_value > filter_value
            elif lookup_expr == 'gte':
                return property_value >= filter_value
            elif lookup_expr == 'lt':
                return property_value < filter_value
            elif lookup_expr == 'lte':
                return property_value <= filter_value
            elif lookup_expr == 'in':
                return property_value in filter_value
            elif lookup_expr == 'isnull':
                return (property_value is None) == filter_value
            else:
                # Default to exact match for unknown lookup expressions
                return property_value == filter_value
                
        except (TypeError, ValueError) as e:
            logger.warning(f"Error comparing property value {property_value} with filter {filter_value} using {lookup_expr}: {e}")
            return False

    def _generate_nested_field_filters(self, field: models.Field, current_depth: int) -> Dict[str, django_filters.Filter]:
        """
        Generates nested field filters for related model fields.
        
        Args:
            field: Django ForeignKey or OneToOneField
            current_depth: Current nesting depth
            
        Returns:
            Dictionary of nested filter name to Filter instance mappings
        """
        nested_filters = {}
        field_name = field.name
        related_model = field.related_model
        
        # Track performance optimization suggestions
        optimization_suggestions = []
        
        # Get all fields from the related model
        for related_field in related_model._meta.get_fields():
            if not hasattr(related_field, 'name') or related_field.many_to_many:
                continue
                
            nested_field_name = f"{field_name}__{related_field.name}"
            
            # Generate filters based on the related field type
            if isinstance(related_field, (models.CharField, models.TextField)):
                nested_filters.update(self._generate_nested_text_filters(nested_field_name, related_field.name))
            elif isinstance(related_field, (models.IntegerField, models.FloatField, models.DecimalField)):
                nested_filters.update(self._generate_nested_numeric_filters(nested_field_name, related_field.name))
            elif isinstance(related_field, (models.DateField, models.DateTimeField)):
                nested_filters.update(self._generate_nested_date_filters(nested_field_name, related_field.name))
            elif isinstance(related_field, models.BooleanField):
                nested_filters.update(self._generate_nested_boolean_filters(nested_field_name, related_field.name))
            elif isinstance(related_field, models.ForeignKey):
                # Add basic foreign key filter
                nested_filters[nested_field_name] = NumberFilter(
                    field_name=nested_field_name,
                    help_text=f'Filter by {nested_field_name} ID'
                )
                
                # Recursively add deeper nested filters if within depth limits
                if current_depth + 1 < self.max_nested_depth:
                    deeper_nested_filters = self._generate_nested_field_filters(
                        related_field, current_depth + 1
                    )
                    # Prefix the deeper nested filters with current field name
                    for deep_filter_name, deep_filter in deeper_nested_filters.items():
                        prefixed_name = f"{field_name}__{deep_filter_name}"
                        # Extract the lookup expression from the filter name
                        if '__' in deep_filter_name:
                            base_field_path = deep_filter_name.rsplit('__', 1)[0]
                            lookup_expr = deep_filter_name.rsplit('__', 1)[1]
                        else:
                            base_field_path = deep_filter_name
                            lookup_expr = 'exact'
                        
                        # Create the correct field path for Django ORM
                        correct_field_path = f"{field_name}__{base_field_path}"
                        
                        # Create a new filter instance with the correct field_name
                        filter_class = type(deep_filter)
                        new_filter = filter_class(
                            field_name=correct_field_path,
                            lookup_expr=lookup_expr,
                            help_text=getattr(deep_filter, 'help_text', f'Filter by {correct_field_path}')
                        )
                        nested_filters[prefixed_name] = new_filter
        
        # Log performance optimization suggestions
        if nested_filters:
            field_path = field_name
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                optimization_suggestions.append(f"select_related('{field_path}')")
            elif hasattr(field, 'related_model'):
                optimization_suggestions.append(f"prefetch_related('{field_path}')")
            
            if optimization_suggestions:
                logger.debug(f"Performance suggestion for {related_model.__name__}: "
                           f"Consider using {', '.join(optimization_suggestions)} for better performance")
        
        return nested_filters

    def analyze_query_performance(self, model: Type[models.Model], filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the performance implications of applied filters and suggest optimizations.
        
        Args:
            model: Django model being filtered
            filters: Dictionary of applied filters
            
        Returns:
            Dictionary containing performance analysis and optimization suggestions
        """
        analysis = {
            'model': model.__name__,
            'total_filters': len(filters),
            'nested_filters': 0,
            'max_depth': 0,
            'select_related_suggestions': set(),
            'prefetch_related_suggestions': set(),
            'potential_n_plus_one_risks': [],
            'performance_score': 'good',  # good, moderate, poor
            'recommendations': []
        }
        
        # Analyze each filter
        for filter_name, filter_value in filters.items():
            if '__' in filter_name:
                # Calculate depth
                depth = filter_name.count('__') - 1  # Subtract 1 for lookup expression
                if depth > 0:
                    # Only count as nested filter if it crosses model boundaries
                    analysis['nested_filters'] += 1
                    analysis['max_depth'] = max(analysis['max_depth'], depth)
                    
                    # Extract field path (remove lookup expression)
                    parts = filter_name.split('__')
                    lookup_expr = parts[-1]
                    field_path_parts = parts[:-1]
                    
                    # Build field path for optimization suggestions
                    current_model = model
                    field_path = []
                    
                    for i, part in enumerate(field_path_parts):
                        try:
                            field = current_model._meta.get_field(part)
                            field_path.append(part)
                            
                            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                                # Forward relationship - suggest select_related
                                path = '__'.join(field_path)
                                analysis['select_related_suggestions'].add(path)
                                current_model = field.related_model
                            elif hasattr(field, 'related_model'):
                                # Reverse relationship - suggest prefetch_related
                                path = '__'.join(field_path)
                                analysis['prefetch_related_suggestions'].add(path)
                                analysis['potential_n_plus_one_risks'].append(path)
                                current_model = field.related_model
                        except:
                            break
        
        # Calculate performance score
        if analysis['max_depth'] > 3 or analysis['nested_filters'] > 10:
            analysis['performance_score'] = 'poor'
        elif analysis['max_depth'] > 2 or analysis['nested_filters'] > 5:
            analysis['performance_score'] = 'moderate'
        
        # Generate recommendations
        if analysis['select_related_suggestions']:
            select_related_list = sorted(analysis['select_related_suggestions'])
            analysis['recommendations'].append(
                f"Use select_related({', '.join(repr(s) for s in select_related_list)}) "
                f"to optimize forward relationship queries"
            )
        
        if analysis['prefetch_related_suggestions']:
            prefetch_related_list = sorted(analysis['prefetch_related_suggestions'])
            analysis['recommendations'].append(
                f"Use prefetch_related({', '.join(repr(p) for p in prefetch_related_list)}) "
                f"to optimize reverse relationship queries"
            )
        
        if analysis['potential_n_plus_one_risks']:
            analysis['recommendations'].append(
                f"Potential N+1 query risks detected in: {', '.join(analysis['potential_n_plus_one_risks'])}"
            )
        
        if analysis['max_depth'] > 3:
            analysis['recommendations'].append(
                f"Consider reducing max_nested_depth from {analysis['max_depth']} to improve performance"
            )
        
        # Convert sets to lists for JSON serialization
        analysis['select_related_suggestions'] = list(analysis['select_related_suggestions'])
        analysis['prefetch_related_suggestions'] = list(analysis['prefetch_related_suggestions'])
        
        # Log performance analysis
        logger.info(f"Performance analysis for {model.__name__}: "
                   f"Score={analysis['performance_score']}, "
                   f"Nested filters={analysis['nested_filters']}, "
                   f"Max depth={analysis['max_depth']}")
        
        return analysis

    def get_optimized_queryset(self, model: Type[models.Model], filters: Dict[str, Any], 
                              base_queryset=None) -> models.QuerySet:
        """
        Get an optimized queryset based on the filters being applied.
        
        Args:
            model: Django model
            filters: Dictionary of filters to be applied
            base_queryset: Optional base queryset to optimize
            
        Returns:
            Optimized QuerySet with appropriate select_related and prefetch_related calls
        """
        if base_queryset is None:
            queryset = model.objects.all()
        else:
            queryset = base_queryset
        
        # Analyze performance implications
        analysis = self.analyze_query_performance(model, filters)
        
        # Apply select_related optimizations
        if analysis['select_related_suggestions']:
            queryset = queryset.select_related(*analysis['select_related_suggestions'])
            logger.debug(f"Applied select_related({analysis['select_related_suggestions']}) to {model.__name__} queryset")
        
        # Apply prefetch_related optimizations
        if analysis['prefetch_related_suggestions']:
            queryset = queryset.prefetch_related(*analysis['prefetch_related_suggestions'])
            logger.debug(f"Applied prefetch_related({analysis['prefetch_related_suggestions']}) to {model.__name__} queryset")
        
        return queryset
        """Generate nested text-specific filters for related fields."""
        # return {
        #     f'{field_name}__contains': CharFilter(
        #         field_name=field_name.replace('__', '__'),
        #         lookup_expr='contains',
        #         help_text=f'Filter {base_field_name} containing the specified text (case-sensitive)'
        #     ),
        #     f'{field_name}__icontains': CharFilter(
        #         field_name=field_name.replace('__', '__'),
        #         lookup_expr='icontains',
        #         help_text=f'Filter {base_field_name} containing the specified text (case-insensitive)'
        #     ),
        #     f'{field_name}__startswith': CharFilter(
        #         field_name=field_name.replace('__', '__'),
        #         lookup_expr='startswith',
        #         help_text=f'Filter {base_field_name} starting with the specified text'
        #     ),
        #     f'{field_name}__endswith': CharFilter(
        #         field_name=field_name.replace('__', '__'),
        #         lookup_expr='endswith',
        #         help_text=f'Filter {base_field_name} ending with the specified text'
        #     ),
        #     f'{field_name}__exact': CharFilter(
        #         field_name=field_name.replace('__', '__'),
        #         lookup_expr='exact',
        #         help_text=f'Filter {base_field_name} with exact match'
        #     ),
        # }

    def _generate_nested_text_filters(self, field_name: str, base_field_name: str) -> Dict[str, CharFilter]:
        """
        Generate nested text-based filters for CharField and TextField.
        
        Args:
            field_name: The nested field name (e.g., 'category__name')
            base_field_name: The base field name (e.g., 'name')
            
        Returns:
            Dictionary of nested text filter mappings
        """
        return {
            f'{field_name}__exact': CharFilter(
                field_name=field_name,
                lookup_expr='exact',
                help_text=f'Exact match for {base_field_name}'
            ),
            field_name: CharFilter(
                field_name=field_name,
                lookup_expr='exact',
                help_text=f'Exact match for {base_field_name}'
            ),
            f'{field_name}__icontains': CharFilter(
                field_name=field_name,
                lookup_expr='icontains',
                help_text=f'Case-insensitive partial match for {base_field_name}'
            ),
            f'{field_name}__istartswith': CharFilter(
                field_name=field_name,
                lookup_expr='istartswith',
                help_text=f'Case-insensitive starts with for {base_field_name}'
            ),
            f'{field_name}__iendswith': CharFilter(
                field_name=field_name,
                lookup_expr='iendswith',
                help_text=f'Case-insensitive ends with for {base_field_name}'
            ),
        }

    def _generate_nested_numeric_filters(self, field_name: str, base_field_name: str) -> Dict[str, NumberFilter]:
        """Generate nested numeric filters for related fields."""
        return {
            f'{field_name}__exact': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='exact',
                help_text=f'Filter {base_field_name} with exact value'
            ),
            f'{field_name}__gt': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='gt',
                help_text=f'Filter {base_field_name} greater than the specified value'
            ),
            f'{field_name}__gte': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='gte',
                help_text=f'Filter {base_field_name} greater than or equal to the specified value'
            ),
            f'{field_name}__lt': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='lt',
                help_text=f'Filter {base_field_name} less than the specified value'
            ),
            f'{field_name}__lte': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='lte',
                help_text=f'Filter {base_field_name} less than or equal to the specified value'
            ),
            f'{field_name}__range': django_filters.RangeFilter(
                field_name=field_name.replace('__', '__'),
                help_text=f'Filter {base_field_name} within the specified range'
            ),
        }

    def _generate_nested_date_filters(self, field_name: str, base_field_name: str) -> Dict[str, DateFilter]:
        """Generate nested date filters for related fields."""
        return {
            f'{field_name}__exact': DateFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='exact',
                help_text=f'Filter {base_field_name} with exact date match'
            ),
            f'{field_name}__gt': DateFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='gt',
                help_text=f'Filter {base_field_name} after the specified date'
            ),
            f'{field_name}__gte': DateFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='gte',
                help_text=f'Filter {base_field_name} on or after the specified date'
            ),
            f'{field_name}__lt': DateFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='lt',
                help_text=f'Filter {base_field_name} before the specified date'
            ),
            f'{field_name}__lte': DateFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='lte',
                help_text=f'Filter {base_field_name} on or before the specified date'
            ),
            f'{field_name}__date': DateFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='date',
                help_text=f'Filter {base_field_name} by date (ignoring time)'
            ),
            f'{field_name}__year': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='year',
                help_text=f'Filter {base_field_name} by year'
            ),
            f'{field_name}__month': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='month',
                help_text=f'Filter {base_field_name} by month'
            ),
            f'{field_name}__day': NumberFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='day',
                help_text=f'Filter {base_field_name} by day'
            ),
        }

    def _generate_nested_boolean_filters(self, field_name: str, base_field_name: str) -> Dict[str, BooleanFilter]:
        """Generate nested boolean filters for related fields."""
        return {
            f'{field_name}__exact': BooleanFilter(
                field_name=field_name,
                lookup_expr='exact',
                help_text=f'Exact match for {base_field_name}'
            ),
            f'{field_name}': BooleanFilter(
                field_name=field_name.replace('__', '__'),
                help_text=f'Filter {base_field_name} by boolean value'
            ),
            f'{field_name}__isnull': BooleanFilter(
                field_name=field_name.replace('__', '__'),
                lookup_expr='isnull',
                help_text=f'Filter {base_field_name} for null/empty values'
            ),
        }

    def _generate_text_filters(self, field_name: str) -> Dict[str, CharFilter]:
        """Generate text-specific filters: contains, icontains, startswith, endswith."""
        return {
            f'{field_name}': CharFilter(
                field_name=field_name,
                help_text=f'Filter {field_name} with basic text matching'
            ),
            f'{field_name}__contains': CharFilter(
                field_name=field_name,
                lookup_expr='contains',
                help_text=f'Filter {field_name} containing the specified text (case-sensitive)'
            ),
            f'{field_name}__icontains': CharFilter(
                field_name=field_name,
                lookup_expr='icontains',
                help_text=f'Filter {field_name} containing the specified text (case-insensitive)'
            ),
            f'{field_name}__startswith': CharFilter(
                field_name=field_name,
                lookup_expr='startswith',
                help_text=f'Filter {field_name} starting with the specified text'
            ),
            f'{field_name}__endswith': CharFilter(
                field_name=field_name,
                lookup_expr='endswith',
                help_text=f'Filter {field_name} ending with the specified text'
            ),
            f'{field_name}__exact': CharFilter(
                field_name=field_name,
                lookup_expr='exact',
                help_text=f'Filter {field_name} with exact match'
            ),
        }

    def _generate_numeric_filters(self, field_name: str) -> Dict[str, NumberFilter]:
        """Generate numeric filters: gt, gte, lt, lte, range."""
        return {
            f'{field_name}': NumberFilter(
                field_name=field_name,
                help_text=f'Filter {field_name} with basic numeric matching'
            ),
            f'{field_name}__gt': NumberFilter(
                field_name=field_name,
                lookup_expr='gt',
                help_text=f'Filter {field_name} greater than the specified value'
            ),
            f'{field_name}__gte': NumberFilter(
                field_name=field_name,
                lookup_expr='gte',
                help_text=f'Filter {field_name} greater than or equal to the specified value'
            ),
            f'{field_name}__lt': NumberFilter(
                field_name=field_name,
                lookup_expr='lt',
                help_text=f'Filter {field_name} less than the specified value'
            ),
            f'{field_name}__lte': NumberFilter(
                field_name=field_name,
                lookup_expr='lte',
                help_text=f'Filter {field_name} less than or equal to the specified value'
            ),
            f'{field_name}__range': django_filters.RangeFilter(
                field_name=field_name,
                help_text=f'Filter {field_name} within the specified range'
            ),
        }

    def _generate_date_filters(self, field_name: str) -> Dict[str, DateFilter]:
        """Generate date filters: year, month, day, range, gt, lt."""
        return {
            f'{field_name}__year': NumberFilter(
                field_name=field_name,
                lookup_expr='year',
                help_text=f'Filter {field_name} by year'
            ),
            f'{field_name}__month': NumberFilter(
                field_name=field_name,
                lookup_expr='month',
                help_text=f'Filter {field_name} by month'
            ),
            f'{field_name}__day': NumberFilter(
                field_name=field_name,
                lookup_expr='day',
                help_text=f'Filter {field_name} by day'
            ),
            f'{field_name}__gt': DateFilter(
                field_name=field_name,
                lookup_expr='gt',
                help_text=f'Filter {field_name} after the specified date'
            ),
            f'{field_name}__lt': DateFilter(
                field_name=field_name,
                lookup_expr='lt',
                help_text=f'Filter {field_name} before the specified date'
            ),
            f'{field_name}__range': django_filters.DateRangeFilter(
                field_name=field_name,
                help_text=f'Filter {field_name} within the specified date range'
            ),
        }

    def _generate_boolean_filters(self, field_name: str) -> Dict[str, BooleanFilter]:
        """Generate boolean filters: exact matching."""
        return {
            f'{field_name}': BooleanFilter(
                field_name=field_name,
                help_text=f'Filter {field_name} by boolean value'
            ),
        }

    def _generate_choice_filters(self, field_name: str, choices: List) -> Dict[str, ChoiceFilter]:
        """Generate choice filters: in, exact."""
        choice_values = [choice[0] for choice in choices]
        return {
            f'{field_name}': ChoiceFilter(
                field_name=field_name,
                choices=choices,
                help_text=f'Filter {field_name} by specific choice'
            ),
            f'{field_name}__in': django_filters.MultipleChoiceFilter(
                field_name=field_name,
                choices=choices,
                help_text=f'Filter {field_name} by multiple choices'
            ),
        }

    def _generate_file_filters(self, field_name: str) -> Dict[str, CharFilter]:
        """Generate file-specific filters: isnull, exact."""
        return {
            f'{field_name}__isnull': BooleanFilter(
                field_name=f'{field_name}__isnull',
                label=f'{field_name.replace("_", " ").title()} Is Null'
            ),
            f'{field_name}__exact': CharFilter(
                field_name=f'{field_name}__exact',
                label=f'{field_name.replace("_", " ").title()} Exact'
            ),
        }

    def _generate_json_filters(self, field_name: str) -> Dict[str, CharFilter]:
        """Generate JSON-specific filters: exact match and null checks."""
        return {
            f'{field_name}': CharFilter(
                field_name=field_name,
                lookup_expr='exact',
                help_text=f'Filter {field_name} with exact JSON match'
            ),
            f'{field_name}__isnull': BooleanFilter(
                field_name=field_name,
                lookup_expr='isnull',
                help_text=f'Filter {field_name} for null/empty values'
            ),
        }

    def _generate_foreign_key_filters(self, field_name: str, related_model: Type[models.Model] = None) -> Dict[str, NumberFilter]:
        """Generate foreign key filters: exact, in."""
        filters = {
            f'{field_name}': NumberFilter(
                field_name=field_name,
                help_text=f'Filter by {field_name} ID'
            ),
        }
        
        # Only add ModelMultipleChoiceFilter if we have the related model
        if related_model:
            filters[f'{field_name}__in'] = django_filters.ModelMultipleChoiceFilter(
                field_name=field_name,
                queryset=related_model.objects.all(),
                to_field_name='pk',
                help_text=f'Filter by multiple {field_name} IDs'
            )
        
        return filters

    def _generate_many_to_many_filters(self, field_name: str, related_model: Type[models.Model]) -> Dict[str, django_filters.Filter]:
        """
        Generate ManyToMany field filters including count filters.
        
        Args:
            field_name: Name of the ManyToMany field
            related_model: Related model class
            
        Returns:
            Dictionary of filter name to Filter instance mappings
        """
        filters = {
            # Basic ManyToMany filters
            f'{field_name}': NumberFilter(
                field_name=field_name,
                help_text=f'Filter by {field_name} ID'
            ),
            f'{field_name}__in': django_filters.ModelMultipleChoiceFilter(
                field_name=field_name,
                queryset=related_model.objects.all(),
                to_field_name='pk',
                help_text=f'Filter by multiple {field_name} IDs'
            ),
            # Count filters for ManyToMany relationships
            f'{field_name}_count': NumberFilter(
                method=f'filter_{field_name}_count',
                help_text=f'Filter by count of {field_name} relationships'
            ),
            f'{field_name}_count__gt': NumberFilter(
                method=f'filter_{field_name}_count_gt',
                help_text=f'Filter by count of {field_name} relationships greater than'
            ),
            f'{field_name}_count__gte': NumberFilter(
                method=f'filter_{field_name}_count_gte',
                help_text=f'Filter by count of {field_name} relationships greater than or equal'
            ),
            f'{field_name}_count__lt': NumberFilter(
                method=f'filter_{field_name}_count_lt',
                help_text=f'Filter by count of {field_name} relationships less than'
            ),
            f'{field_name}_count__lte': NumberFilter(
                method=f'filter_{field_name}_count_lte',
                help_text=f'Filter by count of {field_name} relationships less than or equal'
            ),
        }
        
        return filters

    def _get_basic_filter_lookups(self, field: models.Field) -> List[str]:
        """
        Returns basic filter lookups for django-filter Meta.fields configuration.
        
        Args:
            field: Django model field
            
        Returns:
            List of lookup expressions for the field
        """
        if isinstance(field, (models.CharField, models.TextField)):
            return ['exact', 'icontains', 'startswith', 'endswith']
        elif isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
            return ['exact', 'gt', 'gte', 'lt', 'lte']
        elif isinstance(field, (models.DateField, models.DateTimeField)):
            return ['exact', 'year', 'month', 'day', 'gt', 'lt']
        elif isinstance(field, models.BooleanField):
            return ['exact']
        elif isinstance(field, (models.FileField, models.ImageField)):
            return ['exact', 'isnull']
        elif isinstance(field, models.JSONField):
            return ['exact', 'isnull']
        elif hasattr(field, 'choices') and field.choices:
            return ['exact', 'in']
        elif isinstance(field, models.ForeignKey):
            return ['exact', 'in']
        else:
            return ['exact']

    def generate_complex_filter_input(self, model: Type[models.Model]) -> Type[graphene.InputObjectType]:
        """
        Generates a GraphQL InputObjectType for complex filtering with AND, OR, NOT operations.
        
        Args:
            model: Django model class
            
        Returns:
            GraphQL InputObjectType for complex filtering
        """
        model_name = model.__name__
        filter_set = self.generate_filter_set(model)
        
        # Create basic filter fields
        filter_fields = {}
        for field_name, filter_instance in filter_set.base_filters.items():
            if isinstance(filter_instance, CharFilter):
                filter_fields[field_name] = graphene.String()
            elif isinstance(filter_instance, NumberFilter):
                filter_fields[field_name] = graphene.Float()
            elif isinstance(filter_instance, DateFilter):
                filter_fields[field_name] = graphene.Date()
            elif isinstance(filter_instance, BooleanFilter):
                filter_fields[field_name] = graphene.Boolean()
            elif isinstance(filter_instance, ChoiceFilter):
                filter_fields[field_name] = graphene.String()

        # Create the complex filter input type
        complex_filter_class = type(
            f'{model_name}ComplexFilter',
            (graphene.InputObjectType,),
            {
                **filter_fields,
                'AND': graphene.List(lambda: complex_filter_class),
                'OR': graphene.List(lambda: complex_filter_class),
                'NOT': graphene.Field(lambda: complex_filter_class),
            }
        )

        return complex_filter_class

    def apply_complex_filters(self, queryset: models.QuerySet, filter_input: Dict[str, Any]) -> models.QuerySet:
        """
        Applies complex filters (AND, OR, NOT) to a Django queryset.
        
        Args:
            queryset: Django queryset to filter
            filter_input: Dictionary containing filter criteria
            
        Returns:
            Filtered queryset
        """
        if not filter_input:
            return queryset

        q_objects = Q()

        # Handle AND operations
        if 'AND' in filter_input:
            and_filters = filter_input.pop('AND')
            for and_filter in and_filters:
                and_q = self._build_q_object(and_filter)
                q_objects &= and_q

        # Handle OR operations
        if 'OR' in filter_input:
            or_filters = filter_input.pop('OR')
            or_q = Q()
            for or_filter in or_filters:
                or_q |= self._build_q_object(or_filter)
            q_objects &= or_q

        # Handle NOT operations
        if 'NOT' in filter_input:
            not_filter = filter_input.pop('NOT')
            not_q = self._build_q_object(not_filter)
            q_objects &= ~not_q

        # Handle regular field filters
        regular_q = self._build_q_object(filter_input)
        q_objects &= regular_q

        return queryset.filter(q_objects)

    def _build_q_object(self, filter_dict: Dict[str, Any]) -> Q:
        """
        Builds a Django Q object from a filter dictionary.
        
        Args:
            filter_dict: Dictionary containing filter criteria
            
        Returns:
            Django Q object
        """
        q_object = Q()
        
        for key, value in filter_dict.items():
            if key in ['AND', 'OR', 'NOT']:
                continue  # These are handled separately
            
            if value is not None:
                q_object &= Q(**{key: value})
        
        return q_object

    def _generate_property_filters(self, model: Type[models.Model]) -> Dict[str, django_filters.Filter]:
        """
        Generate filters for @property methods on the model.
        
        Args:
            model: Django model to generate property filters for
            
        Returns:
            Dictionary of property filter name to Filter instance mappings
        """
        filters = {}
        
        # Use ModelIntrospector to detect properties
        introspector = ModelIntrospector(model)
        properties = introspector.properties
        
        for property_name, property_info in properties.items():
            # Generate filters based on property return type
            property_filters = self._generate_property_type_filters(property_name, property_info.return_type)
            filters.update(property_filters)
        
        logger.debug(f"Generated {len(filters)} property filters for {model.__name__}")
        return filters

    def _generate_property_type_filters(self, property_name: str, return_type: Any) -> Dict[str, django_filters.Filter]:
        """
        Generate specific filters based on property return type.
        
        Args:
            property_name: Name of the property
            return_type: Return type annotation of the property
            
        Returns:
            Dictionary of filter name to Filter instance mappings
        """
        filters = {}
        
        # Handle different return types
        if return_type == str or return_type == 'str':
            filters.update(self._generate_property_text_filters(property_name))
        elif return_type == int or return_type == 'int':
            filters.update(self._generate_property_numeric_filters(property_name))
        elif return_type == float or return_type == 'float':
            filters.update(self._generate_property_numeric_filters(property_name))
        elif return_type == bool or return_type == 'bool':
            filters.update(self._generate_property_boolean_filters(property_name))
        elif return_type == list or return_type == 'list':
            # For list properties, provide basic text filtering
            filters.update(self._generate_property_text_filters(property_name))
        else:
            # Default to text filtering for unknown types
            filters.update(self._generate_property_text_filters(property_name))
        
        return filters

    def _generate_property_text_filters(self, property_name: str) -> Dict[str, django_filters.Filter]:
        """Generate text-specific filters for properties: contains, icontains, startswith, endswith."""
        return {
            f'{property_name}': CharFilter(
                method=self._create_property_filter_method(property_name, 'exact'),
                help_text=f'Filter by {property_name} property with exact text matching'
            ),
            f'{property_name}__contains': CharFilter(
                method=self._create_property_filter_method(property_name, 'contains'),
                help_text=f'Filter by {property_name} property containing the specified text (case-sensitive)'
            ),
            f'{property_name}__icontains': CharFilter(
                method=self._create_property_filter_method(property_name, 'icontains'),
                help_text=f'Filter by {property_name} property containing the specified text (case-insensitive)'
            ),
            f'{property_name}__startswith': CharFilter(
                method=self._create_property_filter_method(property_name, 'startswith'),
                help_text=f'Filter by {property_name} property starting with the specified text'
            ),
            f'{property_name}__endswith': CharFilter(
                method=self._create_property_filter_method(property_name, 'endswith'),
                help_text=f'Filter by {property_name} property ending with the specified text'
            ),
            f'{property_name}__exact': CharFilter(
                method=self._create_property_filter_method(property_name, 'exact'),
                help_text=f'Filter by {property_name} property with exact match'
            ),
        }

    def _generate_property_numeric_filters(self, property_name: str) -> Dict[str, django_filters.Filter]:
        """Generate numeric filters for properties: gt, gte, lt, lte."""
        return {
            f'{property_name}': NumberFilter(
                method=self._create_property_filter_method(property_name, 'exact'),
                help_text=f'Filter by {property_name} property with exact numeric matching'
            ),
            f'{property_name}__gt': NumberFilter(
                method=self._create_property_filter_method(property_name, 'gt'),
                help_text=f'Filter by {property_name} property greater than the specified value'
            ),
            f'{property_name}__gte': NumberFilter(
                method=self._create_property_filter_method(property_name, 'gte'),
                help_text=f'Filter by {property_name} property greater than or equal to the specified value'
            ),
            f'{property_name}__lt': NumberFilter(
                method=self._create_property_filter_method(property_name, 'lt'),
                help_text=f'Filter by {property_name} property less than the specified value'
            ),
            f'{property_name}__lte': NumberFilter(
                method=self._create_property_filter_method(property_name, 'lte'),
                help_text=f'Filter by {property_name} property less than or equal to the specified value'
            ),
        }

    def _generate_property_boolean_filters(self, property_name: str) -> Dict[str, django_filters.Filter]:
        """Generate boolean filters for properties."""
        return {
            f'{property_name}': BooleanFilter(
                method=self._create_property_filter_method(property_name, 'exact'),
                help_text=f'Filter by {property_name} property boolean value'
            ),
        }