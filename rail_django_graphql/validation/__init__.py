"""
Schema validation and error handling module.

This module provides comprehensive validation capabilities for GraphQL schemas,
including schema configuration validation, GraphQL schema validation, and
enhanced error handling.
"""

from .schema_validator import SchemaValidator, ValidationResult
from .error_handlers import (
    SchemaRegistryError,
    SchemaValidationError,
    SchemaConflictError,
    ValidationErrorHandler
)

__all__ = [
    'SchemaValidator',
    'ValidationResult',
    'SchemaRegistryError',
    'SchemaValidationError',
    'SchemaConflictError',
    'ValidationErrorHandler'
]