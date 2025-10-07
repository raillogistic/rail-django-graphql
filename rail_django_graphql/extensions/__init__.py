"""
Extensions package for Django GraphQL Auto-Generation.

This package contains extension modules for:
- Authentication and JWT management
- Audit logging and security monitoring
- Multi-factor authentication (MFA)
- Security enhancements
"""

from .auth import (
    UserType,
    AuthPayload,
    JWTManager,
    LoginMutation,
    RegisterMutation,
    RefreshTokenMutation,
    LogoutMutation,
    MeQuery,
    AuthMutations,
    get_user_from_token,
    authenticate_request
)

from .audit import (
    AuditEventType,
    AuditSeverity,
    AuditEvent,
    AuditLogger,
    audit_logger,
    log_authentication_event,
    get_security_dashboard_data
)

from .mfa import (
    MFAManager,
    mfa_manager,
    MFADeviceType,
    TrustedDeviceType,
    SetupTOTPMutation,
    VerifyTOTPMutation,
    MFAMutations,
    MFAQueries
)

__all__ = [
    # Auth module
    'UserType',
    'AuthPayload',
    'JWTManager',
    'LoginMutation',
    'RegisterMutation',
    'RefreshTokenMutation',
    'LogoutMutation',
    'MeQuery',
    'AuthMutations',
    'get_user_from_token',
    'authenticate_request',
    
    # Audit module
    'AuditEventType',
    'AuditSeverity',
    'AuditEvent',
    'AuditLogger',
    'audit_logger',
    'log_authentication_event',
    'get_security_dashboard_data',
    
    # MFA module
    'MFAManager',
    'mfa_manager',
    'MFADeviceType',
    'TrustedDeviceType',
    'SetupTOTPMutation',
    'VerifyTOTPMutation',
    'MFAMutations',
    'MFAQueries'
]