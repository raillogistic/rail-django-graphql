#!/usr/bin/env python
"""
Direct mutation test to see debug logs.
"""

import os
import sys
import django
import logging

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

from test_app.models import Tag
from django_graphql_auto.generators.mutations import MutationGenerator
from django_graphql_auto.generators.types import TypeGenerator

def test_direct_mutation():
    """Test the mutation directly."""
    
    print("Creating mutation generator...")
    type_generator = TypeGenerator()
    mutation_generator = MutationGenerator(type_generator)
    
    print("Generating create mutation for Tag model...")
    create_mutation_class = mutation_generator.generate_create_mutation(Tag)
    
    print(f"Generated mutation class: {create_mutation_class}")
    
    # Create first tag
    tag1 = Tag.objects.create(name="direct_test_unique")
    print(f"Created first tag: {tag1.name}")
    
    # Create mock input as a dictionary (which has items() method)
    mock_input = {"name": "direct_test_unique"}
    
    # Try to create duplicate
    print("\nTesting duplicate creation...")
    
    try:
        # Create a mock info object with context
        class MockContext:
            pass
        
        class MockInfo:
            def __init__(self):
                self.context = MockContext()
        
        mock_info = MockInfo()
        
        result = create_mutation_class.mutate(None, mock_info, input=mock_input)
        print(f"Mutation result: {result}")
        print(f"OK: {result.ok}")
        print(f"Errors: {result.errors}")
        
        if result.errors:
            for error in result.errors:
                print(f"Error field: {error.field}")
                print(f"Error message: {error.message}")
    except Exception as e:
        print(f"Exception during mutation: {e}")
    
    # Clean up
    Tag.objects.filter(name="direct_test_unique").delete()
    print("\nCleanup completed.")

if __name__ == "__main__":
    test_direct_mutation()