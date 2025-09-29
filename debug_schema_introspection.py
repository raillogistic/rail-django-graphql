#!/usr/bin/env python
"""
Debug script to introspect the GraphQL schema and examine the actual input types
being used in the schema, not just what's generated in memory.
"""

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from graphql import build_client_schema, get_introspection_query
from django_graphql_auto.core.schema import SchemaBuilder
import json

def debug_schema_introspection():
    """Debug the actual GraphQL schema introspection to see field requirements."""
    
    print("=== DEBUGGING GRAPHQL SCHEMA INTROSPECTION ===\n")
    
    # Get the schema
    schema_builder = SchemaBuilder()
    schema = schema_builder.get_schema()
    
    print("1. Schema built successfully")
    
    # Execute introspection query
    introspection_query = get_introspection_query()
    result = schema.execute(introspection_query)
    
    if result.errors:
        print(f"Introspection errors: {result.errors}")
        return
    
    schema_dict = result.data
    
    # Find PostInput type in the schema
    types = schema_dict['__schema']['types']
    post_input_types = [t for t in types if t['name'] and 'PostInput' in t['name']]
    
    print(f"2. Found {len(post_input_types)} PostInput types:")
    for input_type in post_input_types:
        print(f"   - {input_type['name']}")
    
    # Examine each PostInput type
    for input_type in post_input_types:
        print(f"\n3. Examining {input_type['name']}:")
        print(f"   Kind: {input_type['kind']}")
        print(f"   Description: {input_type.get('description', 'None')}")
        
        if input_type['inputFields']:
            print("   Fields:")
            for field in input_type['inputFields']:
                field_name = field['name']
                field_type = field['type']
                
                # Check if field is required (NON_NULL wrapper)
                is_required = field_type['kind'] == 'NON_NULL'
                
                # Get the actual type name
                if is_required:
                    actual_type = field_type['ofType']
                else:
                    actual_type = field_type
                
                type_name = actual_type.get('name', 'Unknown')
                if actual_type['kind'] == 'LIST':
                    type_name = f"[{actual_type['ofType'].get('name', 'Unknown')}]"
                
                required_str = "REQUIRED" if is_required else "OPTIONAL"
                print(f"     - {field_name}: {type_name} ({required_str})")
    
    # Look for mutations that use PostInput
    print(f"\n4. Examining mutations that use PostInput:")
    
    mutation_type = None
    for t in types:
        if t['name'] == 'Mutation':
            mutation_type = t
            break
    
    if mutation_type and mutation_type['fields']:
        post_mutations = [f for f in mutation_type['fields'] if 'post' in f['name'].lower()]
        
        for mutation in post_mutations:
            print(f"\n   Mutation: {mutation['name']}")
            if mutation['args']:
                for arg in mutation['args']:
                    arg_name = arg['name']
                    arg_type = arg['type']
                    
                    # Check if argument is required
                    is_required = arg_type['kind'] == 'NON_NULL'
                    
                    # Get the actual type name
                    if is_required:
                        actual_type = arg_type['ofType']
                    else:
                        actual_type = arg_type
                    
                    type_name = actual_type.get('name', 'Unknown')
                    required_str = "REQUIRED" if is_required else "OPTIONAL"
                    
                    print(f"     Argument: {arg_name}: {type_name} ({required_str})")
    
    print("\n=== END SCHEMA INTROSPECTION DEBUG ===")

if __name__ == "__main__":
    debug_schema_introspection()