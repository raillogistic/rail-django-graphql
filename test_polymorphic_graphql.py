#!/usr/bin/env python
"""
GraphQL test to verify polymorphic fields are excluded from mutations.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

import graphene
from rail_django_graphql.core.schema import SchemaBuilder


def test_polymorphic_mutation_schema():
    """Test that polymorphic fields are excluded from the GraphQL schema."""
    print("Testing polymorphic mutation schema...")

    try:
        # Get the schema
        builder = SchemaBuilder()
        schema = builder.get_schema()

        # Get the schema SDL
        schema_sdl = str(schema)

        print("\n1. Checking for polymorphic fields in schema:")

        # Check if polymorphic fields appear in input types
        has_polymorphic_ctype = "polymorphic_ctype" in schema_sdl
        has_client_ptr = "client_ptr" in schema_sdl

        print(f"   polymorphic_ctype in schema: {has_polymorphic_ctype}")
        print(f"   client_ptr in schema: {has_client_ptr}")

        # Look for Client input types specifically
        print("\n2. Checking Client input types:")
        lines = schema_sdl.split("\n")
        in_client_input = False
        client_input_fields = []

        for line in lines:
            line = line.strip()
            if "input" in line.lower() and "client" in line.lower():
                in_client_input = True
                print(f"   Found input type: {line}")
                continue
            elif in_client_input and line == "}":
                in_client_input = False
                continue
            elif in_client_input and ":" in line:
                field_name = line.split(":")[0].strip()
                client_input_fields.append(field_name)
                print(f"     Field: {field_name}")

        # Check if polymorphic fields are in client input fields
        polymorphic_in_inputs = any(
            field in ["polymorphic_ctype", "client_ptr"]
            for field in client_input_fields
        )

        if not polymorphic_in_inputs:
            print("   ✅ SUCCESS: No polymorphic fields found in Client input types")
        else:
            print(
                "   ❌ FAILED: Polymorphic fields still present in Client input types"
            )

        # Test a simple mutation query
        print("\n3. Testing mutation introspection:")

        # Get mutation type
        mutation_type = schema.get_type("Mutation")
        if mutation_type:
            mutation_fields = mutation_type.fields
            client_mutations = [
                name for name in mutation_fields.keys() if "client" in name.lower()
            ]
            print(f"   Client mutations found: {client_mutations}")

            # Check a specific mutation's input type
            if "createClient" in mutation_fields:
                create_client = mutation_fields["createClient"]
                input_arg = create_client.args.get("input")
                if input_arg:
                    input_type = input_arg.type
                    if hasattr(input_type, "fields"):
                        input_field_names = list(input_type.fields.keys())
                        print(f"   createClient input fields: {input_field_names}")

                        polymorphic_in_create = any(
                            field in ["polymorphic_ctype", "client_ptr"]
                            for field in input_field_names
                        )
                        if not polymorphic_in_create:
                            print(
                                "   ✅ SUCCESS: createClient mutation excludes polymorphic fields"
                            )
                        else:
                            print(
                                "   ❌ FAILED: createClient mutation includes polymorphic fields"
                            )

        return not has_polymorphic_ctype and not has_client_ptr

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = test_polymorphic_mutation_schema()
    if success:
        print("\n🎉 All tests passed! Polymorphic fields are properly excluded.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
