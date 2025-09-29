#!/usr/bin/env python3
"""
Simple test to verify polymorphic fields are excluded from GraphQL schema
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.core.schema import SchemaBuilder

def test_polymorphic_exclusion():
    """Test that polymorphic fields are excluded from the schema"""
    print("Testing polymorphic field exclusion...")
    
    try:
        # Get the schema
        builder = SchemaBuilder()
        schema = builder.get_schema()
        
        # Get the schema SDL
        schema_sdl = str(schema)
        
        # Check that polymorphic fields are NOT in the schema
        polymorphic_fields = ['polymorphic_ctype', 'client_ptr']
        
        print("\n1. Checking for polymorphic fields in schema SDL:")
        for field in polymorphic_fields:
            if field in schema_sdl:
                print(f"   ❌ FAILED: Found '{field}' in schema")
                return False
            else:
                print(f"   ✅ PASSED: '{field}' correctly excluded from schema")
        
        # Check that normal fields are still present
        normal_fields = ['raison', 'test', 'info', 'adresse', 'ville']
        
        print("\n2. Checking that normal fields are still present:")
        for field in normal_fields:
            if field in schema_sdl:
                print(f"   ✅ PASSED: '{field}' found in schema")
            else:
                print(f"   ⚠️  WARNING: '{field}' not found in schema")
        
        print("\n✅ All tests passed! Polymorphic fields are correctly excluded.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_polymorphic_exclusion()
    sys.exit(0 if success else 1)