"""
Tests for method-to-mutation conversion functionality.
Tests the enhanced MutationGenerator with business logic decorators.
"""

import pytest
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
import graphene
from graphene.test import Client

from django_graphql_auto.generators.mutations import MutationGenerator
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.introspector import ModelIntrospector
from django_graphql_auto.core.settings import MutationGeneratorSettings
from django_graphql_auto.decorators import mutation, business_logic, custom_mutation_name
from test_app.models import Post, Category, Tag, Comment, Profile


class TestMethodMutationGeneration(TestCase):
    """Test method-to-mutation conversion functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test description'
        )
        self.tag = Tag.objects.create(
            name='test-tag',
            color='#FF0000'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content for the post',
            author=self.user,
            category=self.category
        )
        
        # Set up generators
        self.type_generator = TypeGenerator()
        self.settings = MutationGeneratorSettings(
            enable_method_mutations=True
        )
        self.mutation_generator = MutationGenerator(
            type_generator=self.type_generator,
            settings=self.settings
        )
        self.introspector = ModelIntrospector(Post)

    def test_method_detection(self):
        """Test that methods are correctly detected and categorized."""
        methods = self.introspector.get_model_methods()
        
        # Check that decorated methods are detected
        method_names = list(methods.keys())
        self.assertIn('publish_post', method_names)
        self.assertIn('archive_post', method_names)
        self.assertIn('add_tag', method_names)
        self.assertIn('calculate_reading_time', method_names)
        
        # Check mutation detection
        publish_method = methods['publish_post']
        self.assertTrue(publish_method.is_mutation)
        self.assertFalse(publish_method.is_private)
        
        # Check business logic detection
        archive_method = methods['archive_post']
        self.assertTrue(archive_method.is_mutation)

    def test_convert_method_to_mutation_basic(self):
        """Test basic method-to-mutation conversion."""
        # Get a simple method
        methods = self.introspector.get_model_methods()
        calculate_method = methods['calculate_reading_time']
        
        # Convert to mutation
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Post, 'calculate_reading_time'
        )
        
        # Check mutation class properties
        self.assertIsNotNone(mutation_class)
        self.assertTrue(hasattr(mutation_class, 'mutate'))
        self.assertTrue(hasattr(mutation_class.Arguments, 'id'))
        
        # Check return type fields exist on the class
        self.assertTrue(hasattr(mutation_class, 'ok'))
        self.assertTrue(hasattr(mutation_class, 'result'))
        self.assertTrue(hasattr(mutation_class, 'errors'))

    def test_convert_method_with_arguments(self):
        """Test method-to-mutation conversion with arguments."""
        methods = self.introspector.get_model_methods()
        add_tag_method = methods['add_tag']
        
        # Convert to mutation
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Post, 'add_tag'
        )
        
        # Check mutation class properties
        self.assertIsNotNone(mutation_class)
        self.assertTrue(hasattr(mutation_class, 'mutate'))
        self.assertTrue(hasattr(mutation_class.Arguments, 'id'))
        
        # Check return type fields exist on the class
        self.assertTrue(hasattr(mutation_class, 'ok'))
        self.assertTrue(hasattr(mutation_class, 'result'))
        self.assertTrue(hasattr(mutation_class, 'errors'))

    def test_business_logic_mutation_generation(self):
        """Test generation of business logic mutations."""
        methods = self.introspector.get_model_methods()
        publish_method = methods['publish_post']
        
        # Convert to mutation
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Post, 'publish_post'
        )
        
        # Check mutation class properties
        self.assertIsNotNone(mutation_class)
        self.assertTrue(hasattr(mutation_class, 'mutate'))
        self.assertTrue(hasattr(mutation_class.Arguments, 'id'))
        
        # Check return type fields exist on the class
        self.assertTrue(hasattr(mutation_class, 'ok'))
        self.assertTrue(hasattr(mutation_class, 'result'))
        self.assertTrue(hasattr(mutation_class, 'errors'))
        
        # Check that business logic metadata is preserved
        self.assertTrue(hasattr(mutation_class, '_business_logic_category'))
        self.assertEqual(mutation_class._business_logic_category, 'publishing')
        self.assertTrue(hasattr(mutation_class, '_requires_permission'))
        self.assertEqual(mutation_class._requires_permission, 'can_publish_posts')

    def test_custom_mutation_name(self):
        """Test custom mutation name decorator."""
        methods = self.introspector.get_model_methods()
        add_tag_method = methods['add_tag']
        
        # Check that custom name is detected
        self.assertTrue(hasattr(add_tag_method.method, '_custom_mutation_name'))
        self.assertEqual(add_tag_method.method._custom_mutation_name, 'addTagToPost')

    def test_mutation_execution_success(self):
        """Test successful mutation execution."""
        methods = self.introspector.get_model_methods()
        calculate_method = methods['calculate_reading_time']
        
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Post, 'calculate_reading_time'
        )
        
        # Execute mutation
        result = mutation_class.mutate(None, None, id=self.post.id)
        
        # Check result
        self.assertTrue(result.ok)
        self.assertIsNotNone(result.result)
        self.assertEqual(len(result.errors), 0)

    def test_mutation_execution_with_arguments(self):
        """Test mutation execution with arguments."""
        methods = self.introspector.get_model_methods()
        add_tag_method = methods['add_tag']
        
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Post, 'add_tag'
        )
        
        # Execute mutation
        result = mutation_class.mutate(None, None, id=self.post.id, tag_id=self.tag.id)
        
        # Check result
        self.assertTrue(result.ok)
        self.assertIsNotNone(result.result)
        self.assertEqual(len(result.errors), 0)

    def test_mutation_execution_failure(self):
        """Test mutation execution with failure."""
        methods = self.introspector.get_model_methods()
        add_tag_method = methods['add_tag']
        
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Post, 'add_tag'
        )
        
        # Execute mutation with non-existent tag
        result = mutation_class.mutate(None, None, id=self.post.id, tag_id=99999)
        
        # Check result
        self.assertTrue(result.ok)  # Method handles the error gracefully
        self.assertIsNotNone(result.result)
        # The method returns {"success": False, "error": "Tag not found"}

    def test_permission_checking(self):
        """Test permission checking for business logic mutations."""
        methods = self.introspector.get_model_methods()
        publish_method = methods['publish_post']
        
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Post, 'publish_post'
        )
        
        # Mock info object without permission
        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = self.user
        mock_info.context.user.has_perm = Mock(return_value=False)
        
        # Execute mutation
        result = mutation_class.mutate(None, mock_info, id=self.post.id)
        
        # Check that permission error is returned
        self.assertFalse(result.ok)
        self.assertIn('Permission denied', str(result.errors))

    def test_transaction_handling(self):
        """Test transaction handling in mutations."""
        methods = self.introspector.get_model_methods()
        publish_method = methods['publish_post']
        
        with patch('django_graphql_auto.generators.mutations.transaction.atomic') as mock_atomic:
            # Create the mutation class with the patched atomic
            mutation_class = self.mutation_generator.convert_method_to_mutation(
                Post, 'publish_post'
            )
            
            # Mock info object with permission
            mock_info = Mock()
            mock_info.context = Mock()
            mock_info.context.user = self.user
            mock_info.context.user.has_perm = Mock(return_value=True)
            
            # Execute mutation
            result = mutation_class.mutate(None, mock_info, id=self.post.id)
            
            # Check that transaction was used
            mock_atomic.assert_called_once()

    def test_type_conversion(self):
        """Test Python type to GraphQL type conversion."""
        # Test basic types
        self.assertEqual(
            self.mutation_generator._convert_python_type_to_graphql(str),
            graphene.String
        )
        self.assertEqual(
            self.mutation_generator._convert_python_type_to_graphql(int),
            graphene.Int
        )
        self.assertEqual(
            self.mutation_generator._convert_python_type_to_graphql(bool),
            graphene.Boolean
        )
        
        # Test Union types
        from typing import Union
        union_type = self.mutation_generator._convert_python_type_to_graphql(
            Union[str, int]
        )
        # Union types should default to String
        self.assertEqual(union_type, graphene.String)

    def test_generate_all_mutations_includes_methods(self):
        """Test that generate_all_mutations includes method mutations."""
        mutations = self.mutation_generator.generate_all_mutations(Post)
        
        # Check that method mutations are included
        mutation_names = list(mutations.keys())
        
        # Should include method mutations (named as {model_name}_{method_name})
        method_mutation_names = [name for name in mutation_names if 'post_' in name and name not in ['create_post', 'update_post', 'delete_post', 'bulk_create_post', 'bulk_update_post', 'bulk_delete_post']]
        self.assertGreater(len(method_mutation_names), 0)


class TestDecoratorFunctionality(TestCase):
    """Test decorator functionality."""

    def test_mutation_decorator(self):
        """Test @mutation decorator."""
        @mutation(description="Test mutation")
        def test_method(self):
            return True
        
        self.assertTrue(hasattr(test_method, '_is_mutation'))
        self.assertTrue(test_method._is_mutation)
        self.assertEqual(test_method._mutation_description, "Test mutation")

    def test_business_logic_decorator(self):
        """Test @business_logic decorator."""
        @business_logic(category="test", requires_permission="test_perm")
        def test_method(self):
            return True
        
        self.assertTrue(hasattr(test_method, '_is_business_logic'))
        self.assertTrue(test_method._is_business_logic)
        self.assertEqual(test_method._business_logic_category, "test")
        self.assertEqual(test_method._requires_permission, "test_perm")

    def test_custom_mutation_name_decorator(self):
        """Test @custom_mutation_name decorator."""
        @custom_mutation_name("customName")
        def test_method(self):
            return True
        
        self.assertTrue(hasattr(test_method, '_custom_mutation_name'))
        self.assertEqual(test_method._custom_mutation_name, "customName")

    def test_combined_decorators(self):
        """Test combining multiple decorators."""
        @business_logic(category="test")
        @custom_mutation_name("testMutation")
        @mutation(description="Combined test")
        def test_method(self):
            return True
        
        self.assertTrue(test_method._is_mutation)
        self.assertTrue(test_method._is_business_logic)
        self.assertEqual(test_method._custom_mutation_name, "testMutation")
        self.assertEqual(test_method._mutation_description, "Combined test")


class TestCategoryMethodMutations(TestCase):
    """Test method mutations on Category model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name='Test Category',
            description='Test description'
        )
        
        self.type_generator = TypeGenerator()
        self.settings = MutationGeneratorSettings(
            enable_method_mutations=True
        )
        self.mutation_generator = MutationGenerator(
            type_generator=self.type_generator,
            settings=self.settings
        )

    def test_activate_category_mutation(self):
        """Test activate_category method mutation."""
        introspector = ModelIntrospector(Category)
        methods = introspector.get_model_methods()
        
        activate_method = methods['activate_category']
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Category, 'activate_category'
        )
        
        # Deactivate category first
        self.category.is_active = False
        self.category.save()
        
        # Execute mutation
        result = mutation_class.mutate(None, None, id=self.category.id)
        
        # Check result
        self.assertTrue(result.ok)
        self.category.refresh_from_db()
        self.assertTrue(self.category.is_active)

    def test_deactivate_category_mutation(self):
        """Test deactivate_category method mutation with arguments."""
        introspector = ModelIntrospector(Category)
        methods = introspector.get_model_methods()
        
        deactivate_method = methods['deactivate_category']
        mutation_class = self.mutation_generator.convert_method_to_mutation(
            Category, 'deactivate_category'
        )
        
        # Execute mutation
        result = mutation_class.mutate(
            None, 
            None,
            id=self.category.id, 
            reason="Test deactivation"
        )
        
        # Check result
        self.assertTrue(result.ok)
        self.category.refresh_from_db()
        self.assertFalse(self.category.is_active)


if __name__ == '__main__':
    pytest.main([__file__])