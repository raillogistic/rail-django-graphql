"""
Advanced Filtering System for Django GraphQL Auto-Generation

This module provides the FilterGenerator class, which creates sophisticated
GraphQL filters based on Django model field types, supporting complex
filter combinations and field-specific operations.
"""

from typing import Any, Dict, List, Optional, Type, Union
import graphene
from django.db import models
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
import django_filters
from django_filters import FilterSet, CharFilter, NumberFilter, DateFilter, BooleanFilter, ChoiceFilter


class AdvancedFilterGenerator:
    """
    Generates advanced GraphQL filters for Django models based on field types.
    Supports text, numeric, date, boolean, and choice field filtering with
    complex operations like contains, range, and logical combinations.
    """

    def __init__(self):
        self._filter_cache: Dict[Type[models.Model], Type[FilterSet]] = {}

    def generate_filter_set(self, model: Type[models.Model]) -> Type[FilterSet]:
        """
        Generates a comprehensive FilterSet for the given Django model.
        
        Args:
            model: Django model class to generate filters for
            
        Returns:
            FilterSet class with auto-generated filters based on field types
        """
        if model in self._filter_cache:
            return self._filter_cache[model]

        filter_fields = {}
        meta_fields = {}

        for field in model._meta.get_fields():
            if hasattr(field, 'name') and not field.many_to_many:
                field_filters = self._generate_field_filters(field)
                filter_fields.update(field_filters)
                
                # Add basic field name for simple filtering
                meta_fields[field.name] = self._get_basic_filter_lookups(field)

        # Create dynamic FilterSet class
        filter_set_attrs = {
            **filter_fields,
            'Meta': type('Meta', (), {
                'model': model,
                'fields': meta_fields,
                'filter_overrides': {
                    models.ImageField: {
                        'filter_class': CharFilter,
                        'extra': lambda f: {
                            'lookup_expr': 'icontains',
                        },
                    },
                    models.FileField: {
                        'filter_class': CharFilter,
                        'extra': lambda f: {
                            'lookup_expr': 'icontains',
                        },
                    },
                }
            })
        }

        filter_set_class = type(
            f'{model.__name__}FilterSet',
            (FilterSet,),
            filter_set_attrs
        )

        self._filter_cache[model] = filter_set_class
        return filter_set_class

    def _generate_field_filters(self, field: models.Field) -> Dict[str, django_filters.Filter]:
        """
        Generates specific filters based on Django field type.
        
        Args:
            field: Django model field
            
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
        elif hasattr(field, 'choices') and field.choices:
            filters.update(self._generate_choice_filters(field_name, field.choices))
        elif isinstance(field, models.ForeignKey):
            filters.update(self._generate_foreign_key_filters(field_name, field.related_model))

        return filters

    def _generate_text_filters(self, field_name: str) -> Dict[str, CharFilter]:
        """Generate text-specific filters: contains, icontains, startswith, endswith."""
        return {
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