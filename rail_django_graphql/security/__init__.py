"""
Module de sécurité pour Django GraphQL.

Ce module fournit des fonctionnalités de sécurité avancées :
- Validation et assainissement des entrées
- Contrôle d'accès basé sur les rôles (RBAC)
- Permissions au niveau des champs
- Sécurité spécifique à GraphQL
- Journalisation d'audit
"""

from .input_validation import (
    ValidationSeverity,
    ValidationResult,
    InputValidator,
    GraphQLInputSanitizer,
    validate_input
)

from .rbac import (
    RoleType,
    PermissionScope,
    RoleDefinition,
    PermissionContext,
    RoleManager,
    role_manager,
    require_role,
    require_permission
)

from .field_permissions import (
    FieldAccessLevel,
    FieldVisibility,
    FieldPermissionRule,
    FieldContext,
    FieldPermissionManager,
    field_permission_manager,
    field_permission_required,
    mask_sensitive_fields
)

from .graphql_security import (
    SecurityThreatLevel,
    QueryAnalysisResult,
    SecurityConfig,
    GraphQLSecurityAnalyzer,
    QueryComplexityValidationRule,
    create_security_middleware,
    require_introspection_permission,
    default_security_config,
    security_analyzer
)

from .audit_logging import (
    AuditEventType,
    AuditSeverity,
    AuditEvent,
    AuditLogger,
    audit_logger,
    audit_graphql_operation,
    audit_data_modification
)

__all__ = [
    # Input Validation
    'ValidationSeverity',
    'ValidationResult',
    'InputValidator',
    'GraphQLInputSanitizer',
    'validate_input',
    
    # RBAC
    'RoleType',
    'PermissionScope',
    'RoleDefinition',
    'PermissionContext',
    'RoleManager',
    'role_manager',
    'require_role',
    'require_permission',
    
    # Field Permissions
    'FieldAccessLevel',
    'FieldVisibility',
    'FieldPermissionRule',
    'FieldContext',
    'FieldPermissionManager',
    'field_permission_manager',
    'field_permission_required',
    'mask_sensitive_fields',
    
    # GraphQL Security
    'SecurityThreatLevel',
    'QueryAnalysisResult',
    'SecurityConfig',
    'GraphQLSecurityAnalyzer',
    'QueryComplexityValidationRule',
    'create_security_middleware',
    'require_introspection_permission',
    'default_security_config',
    'security_analyzer',
    
    # Audit Logging
    'AuditEventType',
    'AuditSeverity',
    'AuditEvent',
    'AuditLogger',
    'audit_logger',
    'audit_graphql_operation',
    'audit_data_modification',
]