"""
Permission system for Django GraphQL Auto-Generation.

This module provides comprehensive permission checking for GraphQL operations
including field-level, object-level, and operation-level permissions.
"""

import logging
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

import graphene
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import models
from graphene_django import DjangoObjectType

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types d'opérations GraphQL."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class PermissionLevel(Enum):
    """Niveaux de permissions."""
    FIELD = "field"
    OBJECT = "object"
    OPERATION = "operation"


class PermissionResult:
    """Résultat d'une vérification de permission."""
    
    def __init__(self, allowed: bool, reason: str = ""):
        self.allowed = allowed
        self.reason = reason
    
    def __bool__(self):
        return self.allowed


class BasePermissionChecker:
    """Classe de base pour les vérificateurs de permissions."""
    
    def check_permission(self, user: "AbstractUser", obj: Any = None, **kwargs) -> PermissionResult:
        """
        Vérifie les permissions pour un utilisateur.
        
        Args:
            user: Utilisateur à vérifier
            obj: Objet concerné (optionnel)
            **kwargs: Arguments supplémentaires
            
        Returns:
            PermissionResult indiquant si l'accès est autorisé
        """
        raise NotImplementedError("Les sous-classes doivent implémenter check_permission")


class DjangoPermissionChecker(BasePermissionChecker):
    """Vérificateur basé sur les permissions Django."""
    
    def __init__(self, permission_codename: str, model_class: Type[models.Model] = None):
        self.permission_codename = permission_codename
        self.model_class = model_class
    
    def check_permission(self, user: "AbstractUser", obj: Any = None, **kwargs) -> PermissionResult:
        """Vérifie les permissions Django standard."""
        if not user or not user.is_authenticated:
            return PermissionResult(False, "Utilisateur non authentifié")
        
        if user.is_superuser:
            return PermissionResult(True, "Superutilisateur")
        
        # Construction du nom complet de la permission
        if self.model_class:
            app_label = self.model_class._meta.app_label
            model_name = self.model_class._meta.model_name
            full_permission = f"{app_label}.{self.permission_codename}_{model_name}"
        else:
            full_permission = self.permission_codename
        
        if user.has_perm(full_permission):
            return PermissionResult(True, f"Permission {full_permission} accordée")
        
        return PermissionResult(False, f"Permission {full_permission} refusée")


class OwnershipPermissionChecker(BasePermissionChecker):
    """Vérificateur basé sur la propriété de l'objet."""
    
    def __init__(self, owner_field: str = "owner"):
        self.owner_field = owner_field
    
    def check_permission(self, user: "AbstractUser", obj: Any = None, **kwargs) -> PermissionResult:
        """Vérifie si l'utilisateur est propriétaire de l'objet."""
        if not user or not user.is_authenticated:
            return PermissionResult(False, "Utilisateur non authentifié")
        
        if not obj:
            return PermissionResult(True, "Pas d'objet à vérifier")
        
        if user.is_superuser:
            return PermissionResult(True, "Superutilisateur")
        
        # Vérification de la propriété
        owner = getattr(obj, self.owner_field, None)
        if owner == user:
            return PermissionResult(True, "Propriétaire de l'objet")
        
        return PermissionResult(False, "Pas propriétaire de l'objet")


class CustomPermissionChecker(BasePermissionChecker):
    """Vérificateur personnalisé basé sur une fonction."""
    
    def __init__(self, check_function: Callable[["AbstractUser", Any], bool], description: str = ""):
        self.check_function = check_function
        self.description = description
    
    def check_permission(self, user: "AbstractUser", obj: Any = None, **kwargs) -> PermissionResult:
        """Utilise une fonction personnalisée pour vérifier les permissions."""
        try:
            allowed = self.check_function(user, obj)
            return PermissionResult(
                allowed, 
                f"Vérification personnalisée: {self.description}"
            )
        except Exception as e:
            logger.error(f"Erreur dans la vérification personnalisée: {e}")
            return PermissionResult(False, "Erreur dans la vérification des permissions")


class PermissionManager:
    """Gestionnaire central des permissions."""
    
    def __init__(self):
        self._field_permissions: Dict[str, Dict[str, List[BasePermissionChecker]]] = {}
        self._object_permissions: Dict[str, List[BasePermissionChecker]] = {}
        self._operation_permissions: Dict[str, Dict[str, List[BasePermissionChecker]]] = {}
    
    def register_field_permission(self, model_name: str, field_name: str, 
                                checker: BasePermissionChecker):
        """
        Enregistre une permission au niveau d'un champ.
        
        Args:
            model_name: Nom du modèle
            field_name: Nom du champ
            checker: Vérificateur de permission
        """
        if model_name not in self._field_permissions:
            self._field_permissions[model_name] = {}
        
        if field_name not in self._field_permissions[model_name]:
            self._field_permissions[model_name][field_name] = []
        
        self._field_permissions[model_name][field_name].append(checker)
        logger.info(f"Permission de champ enregistrée: {model_name}.{field_name}")
    
    def register_object_permission(self, model_name: str, checker: BasePermissionChecker):
        """
        Enregistre une permission au niveau d'un objet.
        
        Args:
            model_name: Nom du modèle
            checker: Vérificateur de permission
        """
        if model_name not in self._object_permissions:
            self._object_permissions[model_name] = []
        
        self._object_permissions[model_name].append(checker)
        logger.info(f"Permission d'objet enregistrée: {model_name}")
    
    def register_operation_permission(self, model_name: str, operation: OperationType,
                                    checker: BasePermissionChecker):
        """
        Enregistre une permission au niveau d'une opération.
        
        Args:
            model_name: Nom du modèle
            operation: Type d'opération
            checker: Vérificateur de permission
        """
        if model_name not in self._operation_permissions:
            self._operation_permissions[model_name] = {}
        
        op_key = operation.value
        if op_key not in self._operation_permissions[model_name]:
            self._operation_permissions[model_name][op_key] = []
        
        self._operation_permissions[model_name][op_key].append(checker)
        logger.info(f"Permission d'opération enregistrée: {model_name}.{op_key}")
    
    def check_field_permission(self, user: "AbstractUser", model_name: str, field_name: str,
                             obj: Any = None) -> PermissionResult:
        """
        Vérifie les permissions pour un champ spécifique.
        
        Args:
            user: Utilisateur
            model_name: Nom du modèle
            field_name: Nom du champ
            obj: Instance de l'objet
            
        Returns:
            PermissionResult
        """
        checkers = self._field_permissions.get(model_name, {}).get(field_name, [])
        
        if not checkers:
            return PermissionResult(True, "Aucune restriction de champ")
        
        for checker in checkers:
            result = checker.check_permission(user, obj)
            if not result.allowed:
                return result
        
        return PermissionResult(True, "Toutes les vérifications de champ réussies")
    
    def check_object_permission(self, user: "AbstractUser", model_name: str, 
                              obj: Any = None) -> PermissionResult:
        """
        Vérifie les permissions pour un objet.
        
        Args:
            user: Utilisateur
            model_name: Nom du modèle
            obj: Instance de l'objet
            
        Returns:
            PermissionResult
        """
        checkers = self._object_permissions.get(model_name, [])
        
        if not checkers:
            return PermissionResult(True, "Aucune restriction d'objet")
        
        for checker in checkers:
            result = checker.check_permission(user, obj)
            if not result.allowed:
                return result
        
        return PermissionResult(True, "Toutes les vérifications d'objet réussies")
    
    def check_operation_permission(self, user: "AbstractUser", model_name: str, 
                                 operation: OperationType, obj: Any = None) -> PermissionResult:
        """
        Vérifie les permissions pour une opération.
        
        Args:
            user: Utilisateur
            model_name: Nom du modèle
            operation: Type d'opération
            obj: Instance de l'objet
            
        Returns:
            PermissionResult
        """
        checkers = self._operation_permissions.get(model_name, {}).get(operation.value, [])
        
        if not checkers:
            return PermissionResult(True, "Aucune restriction d'opération")
        
        for checker in checkers:
            result = checker.check_permission(user, obj)
            if not result.allowed:
                return result
        
        return PermissionResult(True, "Toutes les vérifications d'opération réussies")


# Instance globale du gestionnaire de permissions
permission_manager = PermissionManager()


def require_permission(checker: BasePermissionChecker, level: PermissionLevel = PermissionLevel.OPERATION):
    """
    Décorateur pour exiger des permissions sur les mutations GraphQL.
    
    Args:
        checker: Vérificateur de permission
        level: Niveau de permission
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, info, *args, **kwargs):
            user = getattr(info.context, 'user', None)
            
            # Récupération de l'objet si disponible
            obj = None
            if 'id' in kwargs:
                model_class = getattr(self, 'model_class', None)
                if model_class:
                    try:
                        obj = model_class.objects.get(id=kwargs['id'])
                    except model_class.DoesNotExist:
                        pass
            
            result = checker.check_permission(user, obj)
            if not result.allowed:
                logger.warning(f"Permission refusée: {result.reason}")
                raise PermissionDenied(result.reason)
            
            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator


def require_authentication(func):
    """Décorateur pour exiger une authentification."""
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        return func(self, info, *args, **kwargs)
    return wrapper


def require_superuser(func):
    """Décorateur pour exiger les droits de superutilisateur."""
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_superuser:
            raise PermissionDenied("Droits de superutilisateur requis")
        return func(self, info, *args, **kwargs)
    return wrapper


class PermissionFilterMixin:
    """Mixin pour filtrer les objets selon les permissions."""
    
    @classmethod
    def filter_queryset_by_permissions(cls, queryset, user: "AbstractUser", operation: OperationType):
        """
        Filtre un queryset selon les permissions de l'utilisateur.
        
        Args:
            queryset: QuerySet à filtrer
            user: Utilisateur
            operation: Type d'opération
            
        Returns:
            QuerySet filtré
        """
        if not user or not user.is_authenticated:
            return queryset.none()
        
        if user.is_superuser:
            return queryset
        
        # Ici, on peut implémenter une logique de filtrage plus complexe
        # basée sur les permissions de l'utilisateur
        model_name = queryset.model._meta.label_lower
        
        # Vérification des permissions d'opération
        result = permission_manager.check_operation_permission(user, model_name, operation)
        if not result.allowed:
            return queryset.none()
        
        return queryset


def setup_default_permissions():
    """Configure les permissions par défaut pour les modèles Django."""
    
    # Permissions CRUD de base pour tous les modèles
    from django.apps import apps
    
    for model in apps.get_models():
        model_name = model._meta.label_lower
        
        # Permissions CRUD standard
        permission_manager.register_operation_permission(
            model_name, 
            OperationType.CREATE,
            DjangoPermissionChecker("add", model)
        )
        
        permission_manager.register_operation_permission(
            model_name,
            OperationType.READ,
            DjangoPermissionChecker("view", model)
        )
        
        permission_manager.register_operation_permission(
            model_name,
            OperationType.UPDATE,
            DjangoPermissionChecker("change", model)
        )
        
        permission_manager.register_operation_permission(
            model_name,
            OperationType.DELETE,
            DjangoPermissionChecker("delete", model)
        )
        
        permission_manager.register_operation_permission(
            model_name,
            OperationType.LIST,
            DjangoPermissionChecker("view", model)
        )
    
    logger.info("Permissions par défaut configurées pour tous les modèles")


# Configuration automatique des permissions par défaut
try:
    setup_default_permissions()
except Exception as e:
    logger.warning(f"Impossible de configurer les permissions par défaut: {e}")


class PermissionInfo(graphene.ObjectType):
    """Informations sur les permissions d'un utilisateur."""
    
    model_name = graphene.String(description="Nom du modèle")
    can_create = graphene.Boolean(description="Peut créer")
    can_read = graphene.Boolean(description="Peut lire")
    can_update = graphene.Boolean(description="Peut modifier")
    can_delete = graphene.Boolean(description="Peut supprimer")
    can_list = graphene.Boolean(description="Peut lister")


class PermissionQuery(graphene.ObjectType):
    """Queries pour vérifier les permissions."""
    
    my_permissions = graphene.List(
        PermissionInfo,
        model_name=graphene.String(),
        description="Permissions de l'utilisateur connecté"
    )
    
    def resolve_my_permissions(self, info, model_name: str = None):
        """Retourne les permissions de l'utilisateur connecté."""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return []
        
        from django.apps import apps
        models_to_check = []
        
        if model_name:
            try:
                model = apps.get_model(model_name)
                models_to_check = [model]
            except LookupError:
                return []
        else:
            models_to_check = apps.get_models()
        
        permissions = []
        for model in models_to_check:
            model_label = model._meta.label_lower
            
            permissions.append(PermissionInfo(
                model_name=model_label,
                can_create=permission_manager.check_operation_permission(
                    user, model_label, OperationType.CREATE
                ).allowed,
                can_read=permission_manager.check_operation_permission(
                    user, model_label, OperationType.READ
                ).allowed,
                can_update=permission_manager.check_operation_permission(
                    user, model_label, OperationType.UPDATE
                ).allowed,
                can_delete=permission_manager.check_operation_permission(
                    user, model_label, OperationType.DELETE
                ).allowed,
                can_list=permission_manager.check_operation_permission(
                    user, model_label, OperationType.LIST
                ).allowed,
            ))
        
        return permissions