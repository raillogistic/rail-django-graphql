#!/usr/bin/env python
"""
Test script to verify DJANGO_GRAPHQL_AUTO configuration loading.

This script tests that the configuration loader properly reads and applies
the DJANGO_GRAPHQL_AUTO settings, particularly MUTATION_SETTINGS.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')

# Initialize Django
django.setup()

def test_configuration_loading():
    """Test that configuration is properly loaded from Django settings."""
    print("=== Testing DJANGO_GRAPHQL_AUTO Configuration Loading ===\n")
    
    # Import after Django setup
    from django_graphql_auto.core.config_loader import (
        get_django_graphql_auto_settings,
        load_mutation_settings,
        validate_configuration,
        debug_configuration
    )
    
    # Test 1: Check if DJANGO_GRAPHQL_AUTO exists in settings
    print("1. Checking DJANGO_GRAPHQL_AUTO in Django settings...")
    config = get_django_graphql_auto_settings()
    if config:
        print("✓ DJANGO_GRAPHQL_AUTO found in settings")
        print(f"   Config keys: {list(config.keys())}")
    else:
        print("✗ DJANGO_GRAPHQL_AUTO not found in settings")
        return False
    
    # Test 2: Check MUTATION_SETTINGS
    print("\n2. Checking MUTATION_SETTINGS...")
    if 'MUTATION_SETTINGS' in config:
        mutation_config = config['MUTATION_SETTINGS']
        print("✓ MUTATION_SETTINGS found")
        print(f"   Keys: {list(mutation_config.keys())}")
        
        # Check specific settings
        if 'enable_nested_relations' in mutation_config:
            print(f"   enable_nested_relations: {mutation_config['enable_nested_relations']}")
        
        if 'nested_relations_config' in mutation_config:
            print(f"   nested_relations_config: {mutation_config['nested_relations_config']}")
            
        if 'nested_field_config' in mutation_config:
            print(f"   nested_field_config: {mutation_config['nested_field_config']}")
    else:
        print("✗ MUTATION_SETTINGS not found")
        return False
    
    # Test 3: Load MutationGeneratorSettings
    print("\n3. Loading MutationGeneratorSettings...")
    try:
        mutation_settings = load_mutation_settings()
        print("✓ MutationGeneratorSettings loaded successfully")
        print(f"   enable_nested_relations: {mutation_settings.enable_nested_relations}")
        print(f"   nested_relations_config: {mutation_settings.nested_relations_config}")
        print(f"   nested_field_config: {mutation_settings.nested_field_config}")
    except Exception as e:
        print(f"✗ Failed to load MutationGeneratorSettings: {e}")
        return False
    
    # Test 4: Validate configuration
    print("\n4. Validating configuration...")
    is_valid = validate_configuration()
    if is_valid:
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration validation failed")
        return False
    
    # Test 5: Test specific configuration values
    print("\n5. Testing specific configuration values...")
    
    # Test Comment model should be disabled
    if 'Comment' in mutation_settings.nested_relations_config:
        comment_enabled = mutation_settings.nested_relations_config['Comment']
        if comment_enabled == False:
            print("✓ Comment nested relations correctly disabled")
        else:
            print(f"✗ Comment nested relations should be False, got {comment_enabled}")
            return False
    else:
        print("✗ Comment configuration not found in nested_relations_config")
        return False
    
    # Test Post model field configurations
    if 'Post' in mutation_settings.nested_field_config:
        post_config = mutation_settings.nested_field_config['Post']
        expected_post_config = {
            'comments': False,
            'related_posts': False,
            'tags': True,
            'category': True,
            'author': False,
        }
        
        for field, expected_value in expected_post_config.items():
            if field in post_config:
                actual_value = post_config[field]
                if actual_value == expected_value:
                    print(f"✓ Post.{field} correctly set to {expected_value}")
                else:
                    print(f"✗ Post.{field} should be {expected_value}, got {actual_value}")
                    return False
            else:
                print(f"✗ Post.{field} configuration not found")
                return False
    else:
        print("✗ Post configuration not found in nested_field_config")
        return False
    
    # Test Author model field configurations
    if 'Author' in mutation_settings.nested_field_config:
        author_config = mutation_settings.nested_field_config['Author']
        if 'posts' in author_config:
            posts_enabled = author_config['posts']
            if posts_enabled == False:
                print("✓ Author.posts correctly disabled")
            else:
                print(f"✗ Author.posts should be False, got {posts_enabled}")
                return False
        else:
            print("✗ Author.posts configuration not found")
            return False
    else:
        print("✗ Author configuration not found in nested_field_config")
        return False
    
    print("\n=== All Configuration Tests Passed! ===")
    return True


def test_schema_initialization():
    """Test that the schema properly initializes with the loaded configuration."""
    print("\n=== Testing Schema Initialization ===\n")
    
    try:
        from django_graphql_auto.core.schema import SchemaBuilder
        
        print("1. Initializing SchemaBuilder...")
        schema = SchemaBuilder()
        print("✓ Schema initialized successfully")
        
        print("2. Checking mutation generator settings...")
        mutation_generator = schema.mutation_generator
        if hasattr(mutation_generator, 'settings'):
            settings = mutation_generator.settings
            print("✓ Mutation generator has settings")
            print(f"   enable_nested_relations: {settings.enable_nested_relations}")
            print(f"   nested_relations_config: {settings.nested_relations_config}")
            print(f"   nested_field_config: {settings.nested_field_config}")
            
            # Verify the settings match our configuration
            if settings.enable_nested_relations == True:
                print("✓ Global nested relations enabled")
            else:
                print("✗ Global nested relations should be enabled")
                return False
                
            if 'Comment' in settings.nested_relations_config and settings.nested_relations_config['Comment'] == False:
                print("✓ Comment nested relations disabled in schema")
            else:
                print("✗ Comment nested relations not properly disabled in schema")
                return False
                
        else:
            print("✗ Mutation generator missing settings")
            return False
            
        print("\n✓ Schema initialization test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Schema initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all configuration tests."""
    print("Django GraphQL Auto Configuration Test Suite")
    print("=" * 50)
    
    # Run configuration loading tests
    config_test_passed = test_configuration_loading()
    
    if config_test_passed:
        # Run schema initialization tests
        schema_test_passed = test_schema_initialization()
        
        if schema_test_passed:
            print("\n🎉 All tests passed! Configuration is working correctly.")
            return True
        else:
            print("\n❌ Schema initialization tests failed.")
            return False
    else:
        print("\n❌ Configuration loading tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)