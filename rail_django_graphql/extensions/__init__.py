"""Django GraphQL Auto-Generation Extensions Package.

This package provides advanced extensions for Django GraphQL Auto-Generation including:
- JWT-based authentication system with GraphQL mutations
- Multi-factor authentication (MFA) with TOTP, SMS, and backup codes
- Comprehensive audit logging for security events
- Model data export functionality with JWT protection
- Advanced security features and middleware

The extensions are designed to work seamlessly with the core GraphQL auto-generation
functionality while providing enterprise-grade security and monitoring capabilities.
"""

# Core authentication system
# TOTPSetupMutation,
# TOTPVerifyMutation,
# SMSSetupMutation,
# SMSVerifyMutation,
# BackupCodeGenerateMutation,
# BackupCodeVerifyMutation,
# TrustedDeviceManager,
# Audit logging system
from .audit import (
    # AuditLogEntry,
    AuditLogger,
)

# SecurityEvent,
# get_audit_logger,
from .auth import (
    AuthPayload,
    # ChangePasswordMutation,
    JWTManager,
    LoginMutation,
    LogoutMutation,
    RefreshTokenMutation,
    RegisterMutation,
    UserType,
)

# Authentication decorators for Django views
from .auth_decorators import (
    get_user_from_jwt,
    jwt_optional,
    jwt_required,
    require_permissions,
)

# Model export functionality (JWT protected)
from .exporting import (
    ExportView,
    ModelExporter,
    export_model_to_csv,
    export_model_to_excel,
)

# Multi-factor authentication
from .mfa import (
    MFAManager,
)

__all__ = [
    # Authentication
    "JWTManager",
    "AuthPayload",
    "LoginMutation",
    "RegisterMutation",
    "RefreshTokenMutation",
    "LogoutMutation",
    "ChangePasswordMutation",
    "UserType",
    # Authentication decorators
    "jwt_required",
    "jwt_optional",
    "get_user_from_jwt",
    "require_permissions",
    # Multi-factor authentication
    "MFAManager",
    # "TOTPSetupMutation",
    # "TOTPVerifyMutation",
    # "SMSSetupMutation",
    # "SMSVerifyMutation",
    # "BackupCodeGenerateMutation",
    # "BackupCodeVerifyMutation",
    # "TrustedDeviceManager",
    # Audit logging
    "AuditLogger",
    # "SecurityEvent",
    # "AuditLogEntry",
    # "get_audit_logger",
    # Model export (JWT protected)
    "ExportView",
    "ModelExporter",
    "export_model_to_csv",
    "export_model_to_excel",
]
