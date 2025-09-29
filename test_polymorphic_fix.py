#!/usr/bin/env python
"""
Test script to verify that polymorphic fields are properly excluded from mutations.
"""
import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.mutations import MutationGenerator
from test_app.models import Client

def test_polymorphic_field_exclusion():
    """Test that polymorphic fields are excluded from input types."""
    print("Testing polymorphic field exclusion...")
    
    # Initialize generators
    type_generator = TypeGenerator()
    mutation_generator = MutationGenerator(type_generator)
    
    # Test field inclusion check
    print("\n1. Testing _should_include_field method:")
    should_include_polymorphic_ctype = type_generator._should_include_field(Client, 'polymorphic_ctype')
    should_include_client_ptr = type_generator._should_include_field(Client, 'client_ptr')
    should_include_normal_field = type_generator._should_include_field(Client, 'raison')
    
    print(f"   polymorphic_ctype should be excluded: {not should_include_polymorphic_ctype}")
    print(f"   client_ptr should be excluded: {not should_include_client_ptr}")
    print(f"   raison should be included: {should_include_normal_field}")
    
    # Test input type generation
    print("\n2. Testing input type generation:")
    try:
        create_input_type = type_generator.generate_input_type(Client, 'create')
        update_input_type = type_generator.generate_input_type(Client, 'update')
        
        create_fields = list(create_input_type._meta.fields.keys())
        update_fields = list(update_input_type._meta.fields.keys())
        
        print(f"   Create input fields: {create_fields}")
        print(f"   Update input fields: {update_fields}")
        
        # Check that polymorphic fields are not in the input types
        polymorphic_in_create = any(field in create_fields for field in ['polymorphic_ctype', 'client_ptr'])
        polymorphic_in_update = any(field in update_fields for field in ['polymorphic_ctype', 'client_ptr'])
        
        print(f"   Polymorphic fields in create input: {polymorphic_in_create}")
        print(f"   Polymorphic fields in update input: {polymorphic_in_update}")
        
        if not polymorphic_in_create and not polymorphic_in_update:
            print("   ✅ SUCCESS: Polymorphic fields properly excluded from input types")
        else:
            print("   ❌ FAILED: Polymorphic fields still present in input types")
            
    except Exception as e:
        print(f"   ❌ ERROR generating input types: {e}")
    
    # Test mutation generation
    print("\n3. Testing mutation generation:")
    try:
        create_mutation = mutation_generator.generate_create_mutation(Client)
        update_mutation = mutation_generator.generate_update_mutation(Client)
        
        print(f"   Create mutation generated: {create_mutation is not None}")
        print(f"   Update mutation generated: {update_mutation is not None}")
        
        if create_mutation:
            # Get the input argument from the mutation
            input_arg = create_mutation._meta.arguments.get('input')
            if input_arg:
                input_fields = list(input_arg.type._meta.fields.keys())
                print(f"   Create mutation input fields: {input_fields}")
                
                polymorphic_in_mutation = any(field in input_fields for field in ['polymorphic_ctype', 'client_ptr'])
                if not polymorphic_in_mutation:
                    print("   ✅ SUCCESS: Create mutation excludes polymorphic fields")
                else:
                    print("   ❌ FAILED: Create mutation includes polymorphic fields")
        
    except Exception as e:
        print(f"   ❌ ERROR generating mutations: {e}")

if __name__ == "__main__":
    test_polymorphic_field_exclusion()