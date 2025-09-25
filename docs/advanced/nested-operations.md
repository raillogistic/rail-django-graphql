# Nested Operations

This document explains the nested operations system in the Django GraphQL Auto-Generation Library, including nested create, update, and delete operations with complex relationship handling.

## 📚 Table of Contents

- [Overview](#overview)
- [Nested Create Operations](#nested-create-operations)
- [Nested Update Operations](#nested-update-operations)
- [Nested Delete Operations](#nested-delete-operations)
- [Relationship Handling](#relationship-handling)
- [Validation and Error Handling](#validation-and-error-handling)
- [Performance Optimization](#performance-optimization)
- [Configuration](#configuration)
- [Examples](#examples)

## 🔍 Overview

The nested operations system provides:

- **Deep nested creation** with automatic relationship handling
- **Selective nested updates** with partial data support
- **Cascading delete operations** with safety checks
- **Transaction management** for data consistency
- **Validation at all levels** with detailed error reporting
- **Performance optimization** through bulk operations

## 🎯 Nested Create Operations

### Basic Nested Creation

```python
from django_graphql_auto.generators.mutations import NestedMutationGenerator

class NestedCreateMutation:
    """Handles nested object creation with relationship management."""
    
    def __init__(self, model_class, nested_config):
        self.model_class = model_class
        self.nested_config = nested_config
        self.validator = NestedValidator()
    
    def create_with_nested(self, validated_data, context=None):
        """
        Create object with nested relationships.
        
        Args:
            validated_data: Validated input data with nested objects
            context: GraphQL context with user and request info
            
        Returns:
            Created instance with nested objects
        """
        with transaction.atomic():
            # Extract nested data
            nested_data = self._extract_nested_data(validated_data)
            main_data = self._extract_main_data(validated_data)
            
            # Create main instance
            instance = self.model_class.objects.create(**main_data)
            
            # Handle nested relationships
            self._create_nested_relationships(instance, nested_data, context)
            
            # Refresh from database to get all relationships
            instance.refresh_from_db()
            return instance
    
    def _extract_nested_data(self, data):
        """Extract nested relationship data."""
        nested_data = {}
        for field_name, config in self.nested_config.items():
            if field_name in data:
                nested_data[field_name] = data.pop(field_name)
        return nested_data
    
    def _extract_main_data(self, data):
        """Extract main model data."""
        return {k: v for k, v in data.items() 
                if not k.startswith('_') and k not in self.nested_config}
    
    def _create_nested_relationships(self, instance, nested_data, context):
        """Create nested relationships."""
        for field_name, data in nested_data.items():
            config = self.nested_config[field_name]
            field = getattr(self.model_class, field_name)
            
            if config['type'] == 'foreign_key':
                self._create_foreign_key_relation(instance, field_name, data, config, context)
            elif config['type'] == 'one_to_many':
                self._create_one_to_many_relations(instance, field_name, data, config, context)
            elif config['type'] == 'many_to_many':
                self._create_many_to_many_relations(instance, field_name, data, config, context)
    
    def _create_foreign_key_relation(self, instance, field_name, data, config, context):
        """Create foreign key relationship."""
        if data is None:
            return
        
        related_model = config['model']
        
        if isinstance(data, dict):
            # Create new related object
            nested_mutation = NestedCreateMutation(related_model, config.get('nested', {}))
            related_instance = nested_mutation.create_with_nested(data, context)
            setattr(instance, field_name, related_instance)
            instance.save()
        elif isinstance(data, (int, str)):
            # Link to existing object
            try:
                related_instance = related_model.objects.get(pk=data)
                setattr(instance, field_name, related_instance)
                instance.save()
            except related_model.DoesNotExist:
                raise ValidationError(f"{related_model.__name__} with id {data} does not exist")
    
    def _create_one_to_many_relations(self, instance, field_name, data_list, config, context):
        """Create one-to-many relationships."""
        if not data_list:
            return
        
        related_model = config['model']
        foreign_key_field = config['foreign_key_field']
        
        created_objects = []
        for item_data in data_list:
            if isinstance(item_data, dict):
                # Set foreign key reference
                item_data[foreign_key_field] = instance.pk
                
                # Create nested object
                nested_mutation = NestedCreateMutation(related_model, config.get('nested', {}))
                created_obj = nested_mutation.create_with_nested(item_data, context)
                created_objects.append(created_obj)
        
        return created_objects
    
    def _create_many_to_many_relations(self, instance, field_name, data_list, config, context):
        """Create many-to-many relationships."""
        if not data_list:
            return
        
        related_model = config['model']
        manager = getattr(instance, field_name)
        
        created_objects = []
        existing_objects = []
        
        for item_data in data_list:
            if isinstance(item_data, dict):
                # Create new related object
                nested_mutation = NestedCreateMutation(related_model, config.get('nested', {}))
                created_obj = nested_mutation.create_with_nested(item_data, context)
                created_objects.append(created_obj)
            elif isinstance(item_data, (int, str)):
                # Link to existing object
                try:
                    existing_obj = related_model.objects.get(pk=item_data)
                    existing_objects.append(existing_obj)
                except related_model.DoesNotExist:
                    raise ValidationError(f"{related_model.__name__} with id {item_data} does not exist")
        
        # Add all objects to many-to-many relationship
        all_objects = created_objects + existing_objects
        manager.add(*all_objects)
        
        return all_objects
```

### Example: Blog Post with Nested Creation

```python
# Django Models
class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField(blank=True)

class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

class Tag(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#000000')

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# Generated GraphQL Input Types
input CreateAuthorInput {
  name: String!
  email: String!
  bio: String
}

input CreateCategoryInput {
  name: String!
  slug: String!
}

input CreateTagInput {
  name: String!
  color: String
}

input CreateCommentInput {
  authorName: String!
  authorEmail: String!
  content: String!
  isApproved: Boolean
}

input CreatePostInput {
  title: String!
  content: String!
  isPublished: Boolean
  
  # Nested creation options
  author: CreateAuthorInput          # Create new author
  authorId: ID                       # Link to existing author
  
  category: CreateCategoryInput      # Create new category
  categoryId: ID                     # Link to existing category
  
  tags: [CreateTagInput!]           # Create new tags
  tagIds: [ID!]                     # Link to existing tags
  
  comments: [CreateCommentInput!]   # Create nested comments
}

# GraphQL Mutation
mutation {
  createPost(input: {
    title: "Advanced GraphQL Patterns"
    content: "This post explores advanced GraphQL patterns..."
    isPublished: true
    
    # Create new author
    author: {
      name: "John Doe"
      email: "john@example.com"
      bio: "GraphQL expert and developer"
    }
    
    # Link to existing category
    categoryId: "1"
    
    # Mix of new and existing tags
    tags: [
      { name: "GraphQL", color: "#e10098" },
      { name: "Django", color: "#092e20" }
    ]
    tagIds: ["3", "4"]  # Existing tags
    
    # Create nested comments
    comments: [
      {
        authorName: "Jane Smith"
        authorEmail: "jane@example.com"
        content: "Great post! Very informative."
        isApproved: true
      },
      {
        authorName: "Bob Wilson"
        authorEmail: "bob@example.com"
        content: "Looking forward to more content like this."
        isApproved: true
      }
    ]
  }) {
    ok
    post {
      id
      title
      author {
        id
        name
        email
      }
      category {
        id
        name
      }
      tags {
        id
        name
        color
      }
      comments {
        id
        authorName
        content
        isApproved
      }
    }
    errors
  }
}
```

## 🔄 Nested Update Operations

### Selective Nested Updates

```python
class NestedUpdateMutation:
    """Handles nested object updates with relationship management."""
    
    def __init__(self, model_class, nested_config):
        self.model_class = model_class
        self.nested_config = nested_config
        self.validator = NestedValidator()
    
    def update_with_nested(self, instance, validated_data, context=None):
        """
        Update object with nested relationships.
        
        Args:
            instance: Existing instance to update
            validated_data: Validated input data with nested objects
            context: GraphQL context with user and request info
            
        Returns:
            Updated instance with nested objects
        """
        with transaction.atomic():
            # Extract nested data
            nested_data = self._extract_nested_data(validated_data)
            main_data = self._extract_main_data(validated_data)
            
            # Update main instance
            for field, value in main_data.items():
                setattr(instance, field, value)
            instance.save()
            
            # Handle nested relationships
            self._update_nested_relationships(instance, nested_data, context)
            
            # Refresh from database
            instance.refresh_from_db()
            return instance
    
    def _update_nested_relationships(self, instance, nested_data, context):
        """Update nested relationships."""
        for field_name, data in nested_data.items():
            config = self.nested_config[field_name]
            
            if config['type'] == 'foreign_key':
                self._update_foreign_key_relation(instance, field_name, data, config, context)
            elif config['type'] == 'one_to_many':
                self._update_one_to_many_relations(instance, field_name, data, config, context)
            elif config['type'] == 'many_to_many':
                self._update_many_to_many_relations(instance, field_name, data, config, context)
    
    def _update_foreign_key_relation(self, instance, field_name, data, config, context):
        """Update foreign key relationship."""
        if data is None:
            setattr(instance, field_name, None)
            instance.save()
            return
        
        related_model = config['model']
        current_related = getattr(instance, field_name)
        
        if isinstance(data, dict):
            if 'id' in data:
                # Update existing related object
                related_id = data.pop('id')
                try:
                    related_instance = related_model.objects.get(pk=related_id)
                    nested_mutation = NestedUpdateMutation(related_model, config.get('nested', {}))
                    related_instance = nested_mutation.update_with_nested(related_instance, data, context)
                    setattr(instance, field_name, related_instance)
                    instance.save()
                except related_model.DoesNotExist:
                    raise ValidationError(f"{related_model.__name__} with id {related_id} does not exist")
            else:
                # Create new related object
                nested_mutation = NestedCreateMutation(related_model, config.get('nested', {}))
                related_instance = nested_mutation.create_with_nested(data, context)
                setattr(instance, field_name, related_instance)
                instance.save()
        elif isinstance(data, (int, str)):
            # Link to different existing object
            try:
                related_instance = related_model.objects.get(pk=data)
                setattr(instance, field_name, related_instance)
                instance.save()
            except related_model.DoesNotExist:
                raise ValidationError(f"{related_model.__name__} with id {data} does not exist")
    
    def _update_one_to_many_relations(self, instance, field_name, data_list, config, context):
        """Update one-to-many relationships."""
        if data_list is None:
            return
        
        related_model = config['model']
        foreign_key_field = config['foreign_key_field']
        manager = getattr(instance, field_name)
        
        # Get current related objects
        current_objects = list(manager.all())
        current_ids = {obj.id for obj in current_objects}
        
        # Process update data
        updated_ids = set()
        for item_data in data_list:
            if isinstance(item_data, dict):
                if 'id' in item_data:
                    # Update existing object
                    obj_id = item_data.pop('id')
                    try:
                        obj = related_model.objects.get(pk=obj_id)
                        nested_mutation = NestedUpdateMutation(related_model, config.get('nested', {}))
                        nested_mutation.update_with_nested(obj, item_data, context)
                        updated_ids.add(obj_id)
                    except related_model.DoesNotExist:
                        raise ValidationError(f"{related_model.__name__} with id {obj_id} does not exist")
                else:
                    # Create new object
                    item_data[foreign_key_field] = instance.pk
                    nested_mutation = NestedCreateMutation(related_model, config.get('nested', {}))
                    new_obj = nested_mutation.create_with_nested(item_data, context)
                    updated_ids.add(new_obj.id)
        
        # Delete objects not in update list (if configured)
        if config.get('delete_orphans', False):
            orphan_ids = current_ids - updated_ids
            if orphan_ids:
                related_model.objects.filter(id__in=orphan_ids).delete()
    
    def _update_many_to_many_relations(self, instance, field_name, data_list, config, context):
        """Update many-to-many relationships."""
        if data_list is None:
            return
        
        related_model = config['model']
        manager = getattr(instance, field_name)
        
        # Clear existing relationships if configured
        if config.get('replace_all', False):
            manager.clear()
        
        # Process new relationships
        objects_to_add = []
        for item_data in data_list:
            if isinstance(item_data, dict):
                if 'id' in item_data:
                    # Update existing object and add to relationship
                    obj_id = item_data.pop('id')
                    try:
                        obj = related_model.objects.get(pk=obj_id)
                        nested_mutation = NestedUpdateMutation(related_model, config.get('nested', {}))
                        obj = nested_mutation.update_with_nested(obj, item_data, context)
                        objects_to_add.append(obj)
                    except related_model.DoesNotExist:
                        raise ValidationError(f"{related_model.__name__} with id {obj_id} does not exist")
                else:
                    # Create new object and add to relationship
                    nested_mutation = NestedCreateMutation(related_model, config.get('nested', {}))
                    new_obj = nested_mutation.create_with_nested(item_data, context)
                    objects_to_add.append(new_obj)
            elif isinstance(item_data, (int, str)):
                # Add existing object to relationship
                try:
                    obj = related_model.objects.get(pk=item_data)
                    objects_to_add.append(obj)
                except related_model.DoesNotExist:
                    raise ValidationError(f"{related_model.__name__} with id {item_data} does not exist")
        
        # Add objects to relationship
        if objects_to_add:
            manager.add(*objects_to_add)
```

### Example: Update Post with Nested Changes

```python
# GraphQL Input Types for Updates
input UpdateAuthorInput {
  id: ID!
  name: String
  email: String
  bio: String
}

input UpdateCommentInput {
  id: ID
  authorName: String
  authorEmail: String
  content: String
  isApproved: Boolean
}

input UpdatePostInput {
  id: ID!
  title: String
  content: String
  isPublished: Boolean
  
  # Update nested relationships
  author: UpdateAuthorInput        # Update existing author
  authorId: ID                     # Change to different author
  
  categoryId: ID                   # Change category
  
  tagIds: [ID!]                   # Replace all tags
  
  comments: [UpdateCommentInput!] # Update/create comments
}

# GraphQL Mutation
mutation {
  updatePost(input: {
    id: "1"
    title: "Advanced GraphQL Patterns (Updated)"
    content: "This updated post explores even more advanced patterns..."
    
    # Update the author's bio
    author: {
      id: "1"
      bio: "Senior GraphQL expert and Django developer with 10+ years experience"
    }
    
    # Change to different category
    categoryId: "2"
    
    # Replace all tags
    tagIds: ["1", "2", "5"]
    
    # Update comments (mix of updates and new)
    comments: [
      {
        id: "1"
        content: "Great post! Very informative. Thanks for the update!"
        isApproved: true
      },
      {
        # New comment (no id)
        authorName: "Alice Johnson"
        authorEmail: "alice@example.com"
        content: "The updated content is even better!"
        isApproved: true
      }
    ]
  }) {
    ok
    post {
      id
      title
      content
      author {
        id
        name
        bio
      }
      category {
        id
        name
      }
      tags {
        id
        name
      }
      comments {
        id
        authorName
        content
        createdAt
      }
    }
    errors
  }
}
```

## 🗑️ Nested Delete Operations

### Cascading Delete with Safety Checks

```python
class NestedDeleteMutation:
    """Handles nested object deletion with safety checks."""
    
    def __init__(self, model_class, nested_config):
        self.model_class = model_class
        self.nested_config = nested_config
        self.safety_checker = DeletionSafetyChecker()
    
    def delete_with_nested(self, instance, delete_config=None, context=None):
        """
        Delete object with nested relationship handling.
        
        Args:
            instance: Instance to delete
            delete_config: Configuration for nested deletion behavior
            context: GraphQL context with user and request info
            
        Returns:
            Deletion result with affected objects count
        """
        delete_config = delete_config or {}
        
        with transaction.atomic():
            # Check deletion safety
            safety_result = self.safety_checker.check_deletion_safety(
                instance, delete_config, context
            )
            
            if not safety_result.is_safe:
                raise ValidationError(f"Cannot delete: {safety_result.reason}")
            
            # Collect objects to be deleted
            deletion_plan = self._create_deletion_plan(instance, delete_config)
            
            # Execute deletion plan
            result = self._execute_deletion_plan(deletion_plan, context)
            
            return result
    
    def _create_deletion_plan(self, instance, delete_config):
        """Create a plan for nested deletion."""
        plan = DeletionPlan()
        plan.add_primary_target(instance)
        
        # Analyze relationships
        for field_name, config in self.nested_config.items():
            if field_name not in delete_config:
                continue
            
            field_delete_config = delete_config[field_name]
            
            if config['type'] == 'one_to_many':
                self._plan_one_to_many_deletion(
                    plan, instance, field_name, config, field_delete_config
                )
            elif config['type'] == 'many_to_many':
                self._plan_many_to_many_deletion(
                    plan, instance, field_name, config, field_delete_config
                )
        
        return plan
    
    def _plan_one_to_many_deletion(self, plan, instance, field_name, config, delete_config):
        """Plan deletion of one-to-many related objects."""
        manager = getattr(instance, field_name)
        related_objects = manager.all()
        
        if delete_config.get('cascade', False):
            # Delete all related objects
            for obj in related_objects:
                plan.add_cascade_target(obj, field_name)
        elif delete_config.get('set_null', False):
            # Set foreign key to null
            for obj in related_objects:
                plan.add_nullify_target(obj, config['foreign_key_field'])
        elif delete_config.get('protect', True):
            # Protect from deletion if related objects exist
            if related_objects.exists():
                plan.add_protection_violation(
                    f"Cannot delete {instance} because it has related {field_name}"
                )
    
    def _plan_many_to_many_deletion(self, plan, instance, field_name, config, delete_config):
        """Plan deletion of many-to-many relationships."""
        manager = getattr(instance, field_name)
        
        if delete_config.get('clear_relationships', True):
            # Clear many-to-many relationships
            plan.add_relationship_clear(instance, field_name)
        
        if delete_config.get('delete_related', False):
            # Delete related objects (dangerous!)
            related_objects = manager.all()
            for obj in related_objects:
                plan.add_cascade_target(obj, field_name)
    
    def _execute_deletion_plan(self, plan, context):
        """Execute the deletion plan."""
        result = DeletionResult()
        
        # Check for protection violations
        if plan.has_protection_violations():
            raise ValidationError(plan.get_protection_violations())
        
        # Clear many-to-many relationships
        for instance, field_name in plan.get_relationship_clears():
            manager = getattr(instance, field_name)
            count = manager.count()
            manager.clear()
            result.add_cleared_relationships(field_name, count)
        
        # Set foreign keys to null
        for obj, field_name in plan.get_nullify_targets():
            setattr(obj, field_name, None)
            obj.save()
            result.add_nullified_object(obj)
        
        # Delete cascade targets
        for obj, source_field in plan.get_cascade_targets():
            nested_mutation = NestedDeleteMutation(type(obj), {})
            nested_result = nested_mutation.delete_with_nested(obj, {}, context)
            result.merge_cascade_result(source_field, nested_result)
        
        # Delete primary target
        primary_target = plan.get_primary_target()
        primary_target.delete()
        result.add_deleted_object(primary_target)
        
        return result

class DeletionSafetyChecker:
    """Checks if deletion is safe based on relationships and permissions."""
    
    def check_deletion_safety(self, instance, delete_config, context):
        """Check if deletion is safe."""
        result = SafetyCheckResult()
        
        # Check user permissions
        if not self._check_delete_permission(instance, context):
            result.add_violation("User does not have permission to delete this object")
        
        # Check for protected relationships
        self._check_protected_relationships(instance, delete_config, result)
        
        # Check for business rules
        self._check_business_rules(instance, context, result)
        
        return result
    
    def _check_delete_permission(self, instance, context):
        """Check if user has permission to delete the instance."""
        if not context or not hasattr(context, 'user'):
            return True  # No authentication required
        
        user = context.user
        if not user.is_authenticated:
            return False
        
        # Check Django permissions
        app_label = instance._meta.app_label
        model_name = instance._meta.model_name
        permission = f"{app_label}.delete_{model_name}"
        
        return user.has_perm(permission)
    
    def _check_protected_relationships(self, instance, delete_config, result):
        """Check for relationships that would prevent deletion."""
        for field in instance._meta.get_fields():
            if field.is_relation and hasattr(field, 'related_model'):
                if field.one_to_many or field.one_to_one:
                    self._check_reverse_relationship(instance, field, delete_config, result)
    
    def _check_reverse_relationship(self, instance, field, delete_config, result):
        """Check reverse relationship for protection."""
        related_manager = getattr(instance, field.get_accessor_name())
        
        if related_manager.exists():
            field_name = field.get_accessor_name()
            field_config = delete_config.get(field_name, {})
            
            if field_config.get('protect', True) and not field_config.get('cascade', False):
                count = related_manager.count()
                result.add_violation(
                    f"Cannot delete because {count} related {field.related_model.__name__} objects exist"
                )
    
    def _check_business_rules(self, instance, context, result):
        """Check business-specific deletion rules."""
        # Example: Don't allow deletion of published posts
        if hasattr(instance, 'is_published') and instance.is_published:
            result.add_violation("Cannot delete published content")
        
        # Example: Don't allow deletion of objects with recent activity
        if hasattr(instance, 'updated_at'):
            from datetime import timedelta
            if instance.updated_at > timezone.now() - timedelta(hours=1):
                result.add_violation("Cannot delete recently modified objects")
```

### Example: Delete Post with Nested Handling

```python
# GraphQL Input Types for Deletion
input DeletePostInput {
  id: ID!
  
  # Nested deletion configuration
  comments: DeleteCommentsConfig
  tags: DeleteTagsConfig
}

input DeleteCommentsConfig {
  cascade: Boolean      # Delete all comments
  setNull: Boolean      # Set post_id to null (if allowed)
  protect: Boolean      # Prevent deletion if comments exist
}

input DeleteTagsConfig {
  clearRelationships: Boolean  # Clear many-to-many relationships
  deleteRelated: Boolean       # Delete related tags (dangerous!)
}

# GraphQL Mutation
mutation {
  deletePost(input: {
    id: "1"
    
    # Delete all comments when deleting post
    comments: {
      cascade: true
    }
    
    # Clear tag relationships but don't delete tags
    tags: {
      clearRelationships: true
      deleteRelated: false
    }
  }) {
    ok
    deletionResult {
      deletedObjectsCount
      clearedRelationships {
        fieldName
        count
      }
      cascadeResults {
        fieldName
        deletedCount
      }
    }
    errors
  }
}

# Response
{
  "data": {
    "deletePost": {
      "ok": true,
      "deletionResult": {
        "deletedObjectsCount": 1,
        "clearedRelationships": [
          {
            "fieldName": "tags",
            "count": 3
          }
        ],
        "cascadeResults": [
          {
            "fieldName": "comments",
            "deletedCount": 5
          }
        ]
      },
      "errors": []
    }
  }
}
```

## 🔗 Relationship Handling

### Advanced Relationship Management

```python
class RelationshipManager:
    """Manages complex relationship operations."""
    
    def __init__(self):
        self.relationship_handlers = {
            'foreign_key': ForeignKeyHandler(),
            'one_to_many': OneToManyHandler(),
            'many_to_many': ManyToManyHandler(),
            'one_to_one': OneToOneHandler(),
        }
    
    def handle_relationship(self, instance, field_name, data, operation, config):
        """Handle relationship operation."""
        relationship_type = self._get_relationship_type(instance, field_name)
        handler = self.relationship_handlers[relationship_type]
        
        return handler.handle(instance, field_name, data, operation, config)
    
    def _get_relationship_type(self, instance, field_name):
        """Determine the type of relationship."""
        field = instance._meta.get_field(field_name)
        
        if field.many_to_one:
            return 'foreign_key'
        elif field.one_to_many:
            return 'one_to_many'
        elif field.many_to_many:
            return 'many_to_many'
        elif field.one_to_one:
            return 'one_to_one'
        
        raise ValueError(f"Unknown relationship type for field {field_name}")

class ForeignKeyHandler:
    """Handles foreign key relationships."""
    
    def handle(self, instance, field_name, data, operation, config):
        """Handle foreign key operation."""
        if operation == 'create':
            return self._handle_create(instance, field_name, data, config)
        elif operation == 'update':
            return self._handle_update(instance, field_name, data, config)
        elif operation == 'delete':
            return self._handle_delete(instance, field_name, config)
    
    def _handle_create(self, instance, field_name, data, config):
        """Handle foreign key creation."""
        if data is None:
            return None
        
        field = instance._meta.get_field(field_name)
        related_model = field.related_model
        
        if isinstance(data, dict):
            # Create new related object
            related_instance = related_model.objects.create(**data)
            setattr(instance, field_name, related_instance)
            return related_instance
        else:
            # Link to existing object
            related_instance = related_model.objects.get(pk=data)
            setattr(instance, field_name, related_instance)
            return related_instance
    
    def _handle_update(self, instance, field_name, data, config):
        """Handle foreign key update."""
        if data is None:
            setattr(instance, field_name, None)
            return None
        
        field = instance._meta.get_field(field_name)
        related_model = field.related_model
        
        if isinstance(data, dict) and 'id' in data:
            # Update existing related object
            related_id = data.pop('id')
            related_instance = related_model.objects.get(pk=related_id)
            
            for key, value in data.items():
                setattr(related_instance, key, value)
            related_instance.save()
            
            setattr(instance, field_name, related_instance)
            return related_instance
        elif isinstance(data, dict):
            # Create new related object
            related_instance = related_model.objects.create(**data)
            setattr(instance, field_name, related_instance)
            return related_instance
        else:
            # Link to different existing object
            related_instance = related_model.objects.get(pk=data)
            setattr(instance, field_name, related_instance)
            return related_instance
    
    def _handle_delete(self, instance, field_name, config):
        """Handle foreign key deletion."""
        current_related = getattr(instance, field_name)
        
        if current_related and config.get('cascade', False):
            current_related.delete()
        
        setattr(instance, field_name, None)
        return None
```

## ✅ Validation and Error Handling

### Comprehensive Validation System

```python
class NestedValidator:
    """Validates nested operations with detailed error reporting."""
    
    def __init__(self):
        self.errors = []
    
    def validate_nested_data(self, data, model_class, operation='create'):
        """Validate nested operation data."""
        self.errors = []
        
        # Validate main model data
        self._validate_model_data(data, model_class, operation)
        
        # Validate nested relationships
        self._validate_nested_relationships(data, model_class, operation)
        
        if self.errors:
            raise ValidationError(self.errors)
        
        return True
    
    def _validate_model_data(self, data, model_class, operation):
        """Validate main model data."""
        # Check required fields
        if operation == 'create':
            self._check_required_fields(data, model_class)
        
        # Validate field types and constraints
        self._validate_field_constraints(data, model_class)
        
        # Run model-specific validation
        self._run_model_validation(data, model_class, operation)
    
    def _check_required_fields(self, data, model_class):
        """Check that all required fields are present."""
        for field in model_class._meta.get_fields():
            if (not field.null and 
                not field.blank and 
                field.default == models.NOT_PROVIDED and
                field.name not in data):
                self.errors.append(f"Field '{field.name}' is required")
    
    def _validate_field_constraints(self, data, model_class):
        """Validate field-specific constraints."""
        for field_name, value in data.items():
            try:
                field = model_class._meta.get_field(field_name)
                
                # Validate field type
                if not self._is_valid_field_type(value, field):
                    self.errors.append(f"Invalid type for field '{field_name}'")
                
                # Validate field constraints
                self._validate_field_specific_constraints(field_name, value, field)
                
            except FieldDoesNotExist:
                self.errors.append(f"Field '{field_name}' does not exist on {model_class.__name__}")
    
    def _validate_field_specific_constraints(self, field_name, value, field):
        """Validate specific field constraints."""
        if isinstance(field, models.CharField):
            if len(str(value)) > field.max_length:
                self.errors.append(f"Field '{field_name}' exceeds maximum length of {field.max_length}")
        
        elif isinstance(field, models.EmailField):
            from django.core.validators import validate_email
            try:
                validate_email(value)
            except ValidationError:
                self.errors.append(f"Field '{field_name}' is not a valid email address")
        
        elif isinstance(field, models.URLField):
            from django.core.validators import URLValidator
            validator = URLValidator()
            try:
                validator(value)
            except ValidationError:
                self.errors.append(f"Field '{field_name}' is not a valid URL")
    
    def _validate_nested_relationships(self, data, model_class, operation):
        """Validate nested relationship data."""
        for field_name, nested_data in data.items():
            if self._is_relationship_field(model_class, field_name):
                self._validate_relationship_data(field_name, nested_data, model_class, operation)
    
    def _validate_relationship_data(self, field_name, nested_data, model_class, operation):
        """Validate relationship-specific data."""
        try:
            field = model_class._meta.get_field(field_name)
            related_model = field.related_model
            
            if field.many_to_many or field.one_to_many:
                # Validate list of related objects
                if not isinstance(nested_data, list):
                    self.errors.append(f"Field '{field_name}' must be a list")
                    return
                
                for i, item in enumerate(nested_data):
                    if isinstance(item, dict):
                        try:
                            self.validate_nested_data(item, related_model, operation)
                        except ValidationError as e:
                            self.errors.extend([f"{field_name}[{i}]: {error}" for error in e.messages])
            
            else:
                # Validate single related object
                if isinstance(nested_data, dict):
                    try:
                        self.validate_nested_data(nested_data, related_model, operation)
                    except ValidationError as e:
                        self.errors.extend([f"{field_name}: {error}" for error in e.messages])
        
        except FieldDoesNotExist:
            pass  # Already handled in field validation
    
    def _is_relationship_field(self, model_class, field_name):
        """Check if field is a relationship field."""
        try:
            field = model_class._meta.get_field(field_name)
            return field.is_relation
        except FieldDoesNotExist:
            return False
    
    def _is_valid_field_type(self, value, field):
        """Check if value is valid for field type."""
        if value is None:
            return field.null
        
        # Add type checking logic based on field type
        return True  # Simplified for example
    
    def _run_model_validation(self, data, model_class, operation):
        """Run model-specific validation."""
        # Create temporary instance for validation
        if operation == 'create':
            instance = model_class(**data)
        else:
            # For updates, we'd need the existing instance
            instance = model_class()
            for key, value in data.items():
                setattr(instance, key, value)
        
        try:
            instance.full_clean(exclude=self._get_relationship_fields(model_class))
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, messages in e.message_dict.items():
                    self.errors.extend([f"{field}: {msg}" for msg in messages])
            else:
                self.errors.extend(e.messages)
    
    def _get_relationship_fields(self, model_class):
        """Get list of relationship field names."""
        return [
            field.name for field in model_class._meta.get_fields()
            if field.is_relation
        ]
```

## ⚡ Performance Optimization

### Bulk Operations and Query Optimization

```python
class PerformanceOptimizer:
    """Optimizes nested operations for better performance."""
    
    def __init__(self):
        self.bulk_threshold = 10  # Use bulk operations for 10+ objects
    
    def optimize_nested_create(self, data_list, model_class, nested_config):
        """Optimize nested creation for multiple objects."""
        if len(data_list) < self.bulk_threshold:
            # Use individual creation for small batches
            return self._create_individually(data_list, model_class, nested_config)
        else:
            # Use bulk operations for large batches
            return self._create_in_bulk(data_list, model_class, nested_config)
    
    def _create_in_bulk(self, data_list, model_class, nested_config):
        """Create objects in bulk for better performance."""
        with transaction.atomic():
            # Separate main data from nested data
            main_data_list = []
            nested_data_list = []
            
            for data in data_list:
                main_data = {}
                nested_data = {}
                
                for key, value in data.items():
                    if key in nested_config:
                        nested_data[key] = value
                    else:
                        main_data[key] = value
                
                main_data_list.append(main_data)
                nested_data_list.append(nested_data)
            
            # Bulk create main objects
            instances = model_class.objects.bulk_create([
                model_class(**data) for data in main_data_list
            ])
            
            # Handle nested relationships in batches
            self._handle_nested_bulk(instances, nested_data_list, nested_config)
            
            return instances
    
    def _handle_nested_bulk(self, instances, nested_data_list, nested_config):
        """Handle nested relationships for bulk-created objects."""
        for i, (instance, nested_data) in enumerate(zip(instances, nested_data_list)):
            for field_name, data in nested_data.items():
                config = nested_config[field_name]
                
                if config['type'] == 'one_to_many':
                    self._bulk_create_one_to_many(instance, field_name, data, config)
                elif config['type'] == 'many_to_many':
                    self._bulk_create_many_to_many(instance, field_name, data, config)
    
    def _bulk_create_one_to_many(self, instance, field_name, data_list, config):
        """Bulk create one-to-many related objects."""
        if not data_list:
            return
        
        related_model = config['model']
        foreign_key_field = config['foreign_key_field']
        
        # Prepare data for bulk creation
        bulk_data = []
        for item_data in data_list:
            if isinstance(item_data, dict):
                item_data[foreign_key_field] = instance.pk
                bulk_data.append(related_model(**item_data))
        
        if bulk_data:
            related_model.objects.bulk_create(bulk_data)
    
    def _bulk_create_many_to_many(self, instance, field_name, data_list, config):
        """Bulk create many-to-many relationships."""
        if not data_list:
            return
        
        related_model = config['model']
        manager = getattr(instance, field_name)
        
        # Separate new objects from existing IDs
        new_objects = []
        existing_ids = []
        
        for item_data in data_list:
            if isinstance(item_data, dict):
                new_objects.append(related_model(**item_data))
            else:
                existing_ids.append(item_data)
        
        # Bulk create new objects
        if new_objects:
            created_objects = related_model.objects.bulk_create(new_objects)
            manager.add(*created_objects)
        
        # Add existing objects
        if existing_ids:
            existing_objects = related_model.objects.filter(pk__in=existing_ids)
            manager.add(*existing_objects)

class QueryOptimizer:
    """Optimizes database queries for nested operations."""
    
    def optimize_nested_queries(self, queryset, nested_fields):
        """Optimize queryset for nested field access."""
        # Use select_related for foreign keys
        select_related_fields = []
        prefetch_related_fields = []
        
        for field_name in nested_fields:
            field_info = self._get_field_info(queryset.model, field_name)
            
            if field_info['type'] in ['foreign_key', 'one_to_one']:
                select_related_fields.append(field_name)
            elif field_info['type'] in ['one_to_many', 'many_to_many']:
                prefetch_related_fields.append(field_name)
        
        # Apply optimizations
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
        
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)
        
        return queryset
    
    def _get_field_info(self, model, field_name):
        """Get information about a model field."""
        try:
            field = model._meta.get_field(field_name)
            
            if field.many_to_one:
                return {'type': 'foreign_key', 'field': field}
            elif field.one_to_one:
                return {'type': 'one_to_one', 'field': field}
            elif field.one_to_many:
                return {'type': 'one_to_many', 'field': field}
            elif field.many_to_many:
                return {'type': 'many_to_many', 'field': field}
            
        except FieldDoesNotExist:
            pass
        
        return {'type': 'unknown', 'field': None}
```

## ⚙️ Configuration

### Nested Operations Settings

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'NESTED_OPERATIONS': {
        # Enable nested operations
        'ENABLE_NESTED_CREATE': True,
        'ENABLE_NESTED_UPDATE': True,
        'ENABLE_NESTED_DELETE': True,
        
        # Performance settings
        'BULK_THRESHOLD': 10,
        'MAX_NESTING_DEPTH': 5,
        'ENABLE_QUERY_OPTIMIZATION': True,
        
        # Safety settings
        'ENABLE_DELETION_SAFETY_CHECKS': True,
        'DEFAULT_DELETE_PROTECTION': True,
        'REQUIRE_EXPLICIT_CASCADE': True,
        
        # Validation settings
        'ENABLE_NESTED_VALIDATION': True,
        'VALIDATE_RELATIONSHIPS': True,
        'STRICT_TYPE_CHECKING': True,
        
        # Transaction settings
        'USE_TRANSACTIONS': True,
        'TRANSACTION_ISOLATION_LEVEL': 'READ_COMMITTED',
    },
    
    'RELATIONSHIP_HANDLING': {
        # Default behaviors
        'FOREIGN_KEY_ON_DELETE': 'protect',
        'ONE_TO_MANY_ON_DELETE': 'cascade',
        'MANY_TO_MANY_ON_DELETE': 'clear',
        
        # Update behaviors
        'FOREIGN_KEY_ON_UPDATE': 'update',
        'ONE_TO_MANY_ON_UPDATE': 'merge',
        'MANY_TO_MANY_ON_UPDATE': 'replace',
    }
}
```

### Per-Model Configuration

```python
# models.py
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    class GraphQLMeta:
        nested_operations = {
            'comments': {
                'type': 'one_to_many',
                'model': 'Comment',
                'foreign_key_field': 'post',
                'enable_create': True,
                'enable_update': True,
                'enable_delete': True,
                'delete_orphans': True,
                'max_depth': 2,
            },
            'tags': {
                'type': 'many_to_many',
                'model': 'Tag',
                'enable_create': True,
                'enable_update': False,
                'enable_delete': False,
                'replace_all': True,
            },
            'author': {
                'type': 'foreign_key',
                'model': 'Author',
                'enable_create': True,
                'enable_update': True,
                'enable_delete': False,
            }
        }
        
        # Deletion configuration
        deletion_config = {
            'comments': {
                'cascade': True,
                'safety_check': True,
            },
            'tags': {
                'clear_relationships': True,
                'delete_related': False,
            }
        }
```

## 🚀 Next Steps

Now that you understand nested operations:

1. [Learn About Performance Optimization](../development/performance.md) - Optimization techniques
2. [Check Testing Guide](../development/testing.md) - Testing nested operations
3. [Review Troubleshooting Guide](../development/troubleshooting.md) - Common issues and solutions
4. [Explore Advanced Examples](../examples/advanced-examples.md) - Complex nested scenarios

## 🤝 Need Help?

- Check the [API Reference](../api/core-classes.md)
- Review [Configuration Guide](../setup/configuration.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)