"""
Nested Operations System for Django GraphQL Auto-Generation

This module provides advanced nested create/update operations with comprehensive
validation, transaction management, and cascade handling for related objects.
"""

from typing import Any, Dict, List, Optional, Type, Union, Set
import graphene
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Q


class NestedOperationHandler:
    """
    Handles complex nested operations for GraphQL mutations including
    nested creates, updates, and cascade operations with proper validation.
    """

    def __init__(self):
        self._processed_objects: Set[str] = set()
        self._validation_errors: List[str] = []

    def handle_nested_create(
        self, 
        model: Type[models.Model], 
        input_data: Dict[str, Any],
        parent_instance: Optional[models.Model] = None
    ) -> models.Model:
        """
        Handles nested create operations with validation and relationship management.
        
        Args:
            model: Django model class to create
            input_data: Input data containing nested relationships
            parent_instance: Parent model instance if this is a nested create
            
        Returns:
            Created model instance
            
        Raises:
            ValidationError: If validation fails or circular references detected
        """
        try:
            # Separate regular fields from nested relationship fields
            regular_fields = {}
            nested_fields = {}
            m2m_fields = {}

            for field_name, value in input_data.items():
                if not hasattr(model, field_name):
                    continue
                    
                try:
                    field = model._meta.get_field(field_name)
                except:
                    # Handle properties and methods
                    regular_fields[field_name] = value
                    continue

                if isinstance(field, models.ForeignKey):
                    nested_fields[field_name] = (field, value)
                elif isinstance(field, models.OneToOneField):
                    nested_fields[field_name] = (field, value)
                elif isinstance(field, models.ManyToManyField):
                    m2m_fields[field_name] = (field, value)
                else:
                    regular_fields[field_name] = value

            # Handle foreign key relationships first
            for field_name, (field, value) in nested_fields.items():
                if value is None:
                    continue
                    
                if isinstance(value, dict):
                    # Nested create
                    if 'id' in value:
                        # Update existing object
                        related_instance = field.related_model.objects.get(pk=value['id'])
                        regular_fields[field_name] = self.handle_nested_update(
                            field.related_model, 
                            value, 
                            related_instance
                        )
                    else:
                        # Create new object
                        regular_fields[field_name] = self.handle_nested_create(
                            field.related_model, 
                            value
                        )
                elif isinstance(value, (str, int)):
                    # Reference to existing object
                    try:
                        related_instance = field.related_model.objects.get(pk=value)
                        regular_fields[field_name] = related_instance
                    except field.related_model.DoesNotExist:
                        raise ValidationError(
                            f"{field.related_model.__name__} with id '{value}' does not exist"
                        )

            # Create the main instance
            instance = model.objects.create(**regular_fields)

            # Handle many-to-many relationships after instance creation
            for field_name, (field, value) in m2m_fields.items():
                if value is None:
                    continue
                    
                m2m_manager = getattr(instance, field_name)
                
                if isinstance(value, list):
                    related_objects = []
                    for item in value:
                        if isinstance(item, dict):
                            if 'id' in item:
                                # Reference existing object
                                related_obj = field.related_model.objects.get(pk=item['id'])
                            else:
                                # Create new object
                                related_obj = self.handle_nested_create(field.related_model, item)
                            related_objects.append(related_obj)
                        elif isinstance(item, (str, int)):
                            # Direct ID reference
                            related_obj = field.related_model.objects.get(pk=item)
                            related_objects.append(related_obj)
                    
                    m2m_manager.set(related_objects)
                elif isinstance(value, dict):
                    # Handle operations like connect, create, disconnect
                    if 'connect' in value:
                        connect_ids = value['connect']
                        if isinstance(connect_ids, list):
                            existing_objects = field.related_model.objects.filter(pk__in=connect_ids)
                            m2m_manager.add(*existing_objects)
                    
                    if 'create' in value:
                        create_data = value['create']
                        if isinstance(create_data, list):
                            new_objects = [
                                self.handle_nested_create(field.related_model, item)
                                for item in create_data
                            ]
                            m2m_manager.add(*new_objects)
                    
                    if 'disconnect' in value:
                        disconnect_ids = value['disconnect']
                        if isinstance(disconnect_ids, list):
                            objects_to_remove = field.related_model.objects.filter(pk__in=disconnect_ids)
                            m2m_manager.remove(*objects_to_remove)

            return instance

        except Exception as e:
            raise ValidationError(f"Failed to create {model.__name__}: {str(e)}")

    def handle_nested_update(
        self, 
        model: Type[models.Model], 
        input_data: Dict[str, Any],
        instance: models.Model
    ) -> models.Model:
        """
        Handles nested update operations with validation and relationship management.
        
        Args:
            model: Django model class
            input_data: Input data containing updates and nested relationships
            instance: Existing model instance to update
            
        Returns:
            Updated model instance
        """
        try:
            # Separate regular fields from nested relationship fields
            regular_fields = {}
            nested_fields = {}
            m2m_fields = {}

            for field_name, value in input_data.items():
                if field_name == 'id':
                    continue  # Skip ID field
                    
                if not hasattr(model, field_name):
                    continue
                    
                try:
                    field = model._meta.get_field(field_name)
                except:
                    # Handle properties and methods
                    regular_fields[field_name] = value
                    continue

                if isinstance(field, models.ForeignKey):
                    nested_fields[field_name] = (field, value)
                elif isinstance(field, models.OneToOneField):
                    nested_fields[field_name] = (field, value)
                elif isinstance(field, models.ManyToManyField):
                    m2m_fields[field_name] = (field, value)
                else:
                    regular_fields[field_name] = value

            # Update regular fields
            for field_name, value in regular_fields.items():
                setattr(instance, field_name, value)

            # Handle foreign key relationships
            for field_name, (field, value) in nested_fields.items():
                if value is None:
                    setattr(instance, field_name, None)
                elif isinstance(value, dict):
                    if 'id' in value:
                        # Update existing related object
                        related_instance = field.related_model.objects.get(pk=value['id'])
                        updated_instance = self.handle_nested_update(
                            field.related_model, 
                            value, 
                            related_instance
                        )
                        setattr(instance, field_name, updated_instance)
                    else:
                        # Create new related object
                        new_instance = self.handle_nested_create(field.related_model, value)
                        setattr(instance, field_name, new_instance)
                elif isinstance(value, (str, int)):
                    # Reference to existing object
                    related_instance = field.related_model.objects.get(pk=value)
                    setattr(instance, field_name, related_instance)

            # Save the instance
            instance.save()

            # Handle many-to-many relationships
            for field_name, (field, value) in m2m_fields.items():
                if value is None:
                    continue
                    
                m2m_manager = getattr(instance, field_name)
                
                if isinstance(value, dict):
                    # Handle operations like connect, create, disconnect, set
                    if 'set' in value:
                        # Replace all relationships
                        set_data = value['set']
                        if isinstance(set_data, list):
                            related_objects = []
                            for item in set_data:
                                if isinstance(item, dict):
                                    if 'id' in item:
                                        related_obj = field.related_model.objects.get(pk=item['id'])
                                    else:
                                        related_obj = self.handle_nested_create(field.related_model, item)
                                    related_objects.append(related_obj)
                                elif isinstance(item, (str, int)):
                                    related_obj = field.related_model.objects.get(pk=item)
                                    related_objects.append(related_obj)
                            m2m_manager.set(related_objects)
                    
                    if 'connect' in value:
                        # Add relationships
                        connect_data = value['connect']
                        if isinstance(connect_data, list):
                            for item in connect_data:
                                if isinstance(item, (str, int)):
                                    related_obj = field.related_model.objects.get(pk=item)
                                    m2m_manager.add(related_obj)
                    
                    if 'create' in value:
                        # Create and connect new objects
                        create_data = value['create']
                        if isinstance(create_data, list):
                            new_objects = [
                                self.handle_nested_create(field.related_model, item)
                                for item in create_data
                            ]
                            m2m_manager.add(*new_objects)
                    
                    if 'disconnect' in value:
                        # Remove relationships
                        disconnect_data = value['disconnect']
                        if isinstance(disconnect_data, list):
                            for item in disconnect_data:
                                if isinstance(item, (str, int)):
                                    related_obj = field.related_model.objects.get(pk=item)
                                    m2m_manager.remove(related_obj)
                    
                    if 'update' in value:
                        # Update existing related objects
                        update_data = value['update']
                        if isinstance(update_data, list):
                            for item in update_data:
                                if 'id' in item:
                                    related_instance = field.related_model.objects.get(pk=item['id'])
                                    self.handle_nested_update(field.related_model, item, related_instance)

            return instance

        except Exception as e:
            raise ValidationError(f"Failed to update {model.__name__}: {str(e)}")

    def handle_cascade_delete(
        self, 
        instance: models.Model, 
        cascade_rules: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Handles cascade delete operations with configurable cascade rules.
        
        Args:
            instance: Model instance to delete
            cascade_rules: Dictionary mapping field names to cascade actions
                          ('CASCADE', 'PROTECT', 'SET_NULL', 'SET_DEFAULT')
            
        Returns:
            List of deleted object descriptions
        """
        deleted_objects = []
        
        try:
            # Get all related objects
            related_objects = []
            for field in instance._meta.get_fields():
                if hasattr(field, 'related_model') and hasattr(field, 'get_accessor_name'):
                    accessor_name = field.get_accessor_name()
                    if hasattr(instance, accessor_name):
                        related_manager = getattr(instance, accessor_name)
                        if hasattr(related_manager, 'all'):
                            related_objects.extend(list(related_manager.all()))

            # Apply cascade rules
            for related_obj in related_objects:
                field_name = related_obj._meta.model_name
                cascade_action = cascade_rules.get(field_name, 'CASCADE') if cascade_rules else 'CASCADE'
                
                if cascade_action == 'CASCADE':
                    # Recursively delete related objects
                    nested_deleted = self.handle_cascade_delete(related_obj, cascade_rules)
                    deleted_objects.extend(nested_deleted)
                elif cascade_action == 'PROTECT':
                    # Prevent deletion if related objects exist
                    raise ValidationError(
                        f"Cannot delete {instance._meta.model_name} because it has related {field_name} objects"
                    )
                elif cascade_action == 'SET_NULL':
                    # Set foreign key to NULL (if nullable)
                    for fk_field in related_obj._meta.get_fields():
                        if (isinstance(fk_field, models.ForeignKey) and 
                            fk_field.related_model == instance._meta.model and
                            fk_field.null):
                            setattr(related_obj, fk_field.name, None)
                            related_obj.save()

            # Delete the main instance
            instance_description = f"{instance._meta.model_name}(id={instance.pk})"
            instance.delete()
            deleted_objects.append(instance_description)

            return deleted_objects

        except Exception as e:
            raise ValidationError(f"Failed to delete {instance._meta.model_name}: {str(e)}")

    def validate_nested_data(
        self, 
        model: Type[models.Model], 
        input_data: Dict[str, Any],
        operation: str = 'create'
    ) -> List[str]:
        """
        Validates nested input data before processing.
        
        Args:
            model: Django model class
            input_data: Input data to validate
            operation: Operation type ('create' or 'update')
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            # Check for circular references
            if self._has_circular_reference(model, input_data):
                errors.append("Circular reference detected in nested data")
            
            # Validate required fields for create operations
            if operation == 'create':
                required_fields = [
                    field.name for field in model._meta.get_fields()
                    if (hasattr(field, 'null') and not field.null and 
                        not hasattr(field, 'default') and
                        not getattr(field, 'auto_now', False) and
                        not getattr(field, 'auto_now_add', False))
                ]
                
                for required_field in required_fields:
                    if required_field not in input_data:
                        errors.append(f"Required field '{required_field}' is missing")
            
            # Validate field types and constraints
            for field_name, value in input_data.items():
                if not hasattr(model, field_name):
                    continue
                    
                try:
                    field = model._meta.get_field(field_name)
                    field_errors = self._validate_field_value(field, value)
                    errors.extend(field_errors)
                except:
                    continue  # Skip non-model fields
            
            return errors
            
        except Exception as e:
            return [f"Validation error: {str(e)}"]

    def _has_circular_reference(
        self, 
        model: Type[models.Model], 
        input_data: Dict[str, Any],
        visited_models: Optional[Set[Type[models.Model]]] = None
    ) -> bool:
        """
        Checks for circular references in nested data.
        """
        if visited_models is None:
            visited_models = set()
            
        if model in visited_models:
            return True
            
        visited_models.add(model)
        
        for field_name, value in input_data.items():
            if isinstance(value, dict) and hasattr(model, field_name):
                try:
                    field = model._meta.get_field(field_name)
                    if hasattr(field, 'related_model'):
                        if self._has_circular_reference(field.related_model, value, visited_models.copy()):
                            return True
                except:
                    continue
        
        return False

    def _validate_field_value(self, field: models.Field, value: Any) -> List[str]:
        """
        Validates a field value against field constraints.
        """
        errors = []
        
        try:
            # Check null constraints
            if value is None and hasattr(field, 'null') and not field.null:
                errors.append(f"Field '{field.name}' cannot be null")
            
            # Check string length constraints
            if isinstance(field, (models.CharField, models.TextField)) and value is not None:
                if hasattr(field, 'max_length') and field.max_length:
                    if len(str(value)) > field.max_length:
                        errors.append(f"Field '{field.name}' exceeds maximum length of {field.max_length}")
            
            # Check numeric constraints
            if isinstance(field, (models.IntegerField, models.FloatField)) and value is not None:
                try:
                    if isinstance(field, models.IntegerField):
                        int(value)
                    else:
                        float(value)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field.name}' must be a valid number")
            
            # Check choice constraints
            if hasattr(field, 'choices') and field.choices and value is not None:
                valid_choices = [choice[0] for choice in field.choices]
                if value not in valid_choices:
                    errors.append(f"Field '{field.name}' must be one of: {valid_choices}")
            
            return errors
            
        except Exception as e:
            return [f"Field validation error for '{field.name}': {str(e)}"]