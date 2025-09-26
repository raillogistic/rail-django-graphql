"""
Decorators for enhancing Django model methods with GraphQL mutation capabilities.
"""

from functools import wraps
from typing import Any, Callable, Optional, Type
import graphene


def mutation(
    input_type: Optional[Type[graphene.InputObjectType]] = None,
    output_type: Optional[Type[graphene.ObjectType]] = None,
    description: Optional[str] = None
):
    """
    Decorator to mark a model method as a GraphQL mutation.
    
    Args:
        input_type: Custom input type for the mutation
        output_type: Custom output type for the mutation  
        description: Description for the mutation
        
    Example:
        @mutation(description="Activate user account")
        def activate_account(self, reason: str = "Manual activation"):
            self.is_active = True
            self.activation_reason = reason
            self.save()
            return True
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Mark the function as a mutation
        wrapper._is_mutation = True
        wrapper._mutation_input_type = input_type
        wrapper._mutation_output_type = output_type
        wrapper._mutation_description = description or func.__doc__
        
        return wrapper
    return decorator


def business_logic(
    category: str = "general",
    requires_permission: Optional[str] = None,
    atomic: bool = True
):
    """
    Decorator to mark a method as custom business logic that should be exposed as a mutation.
    
    Args:
        category: Category of business logic (e.g., "workflow", "approval", "processing")
        requires_permission: Permission required to execute this mutation
        atomic: Whether to wrap execution in a database transaction
        
    Example:
        @business_logic(category="approval", requires_permission="can_approve_posts")
        def approve_post(self, approved_by: str, notes: str = ""):
            self.status = "approved"
            self.approved_by = approved_by
            self.approval_notes = notes
            self.approved_at = timezone.now()
            self.save()
            return {"status": "approved", "message": "Post approved successfully"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Mark as both mutation and business logic
        wrapper._is_mutation = True
        wrapper._is_business_logic = True
        wrapper._business_logic_category = category
        wrapper._requires_permission = requires_permission
        wrapper._atomic = atomic
        
        return wrapper
    return decorator


def private_method(func: Callable) -> Callable:
    """
    Decorator to mark a method as private (should not be exposed as a mutation).
    
    Example:
        @private_method
        def _internal_calculation(self):
            return self.value * 2
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapper._private = True
    return wrapper


def custom_mutation_name(name: str):
    """
    Decorator to specify a custom name for the generated mutation.
    
    Args:
        name: Custom name for the mutation
        
    Example:
        @custom_mutation_name("publishArticle")
        def publish(self):
            self.is_published = True
            self.published_at = timezone.now()
            self.save()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper._custom_mutation_name = name
        return wrapper
    return decorator