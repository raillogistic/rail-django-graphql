#!/usr/bin/env python3
"""
Test to verify polymorphic_type field is added to the GraphQL schema.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

if not settings.configured:
    django.setup()

from rail_django_graphql.core.schema import SchemaBuilder


def test_polymorphic_type_in_schema():
    """Test that polymorphic_type field is added to ClientType in the schema."""

    try:
        # Build schema
        schema_builder = SchemaBuilder()
        schema = schema_builder.get_schema()

        # Get schema SDL
        schema_sdl = str(schema)

        print("=== Checking Schema for polymorphic_type field ===")

        # Look for ClientType definition
        lines = schema_sdl.split("\n")
        in_client_type = False
        client_type_fields = []

        for line in lines:
            line = line.strip()
            if line.startswith("type ClientType"):
                in_client_type = True
                print(f"Found ClientType definition: {line}")
                continue
            elif in_client_type and line.startswith("}"):
                in_client_type = False
                break
            elif in_client_type and ":" in line:
                client_type_fields.append(line)

        print(f"\nClientType fields found:")
        for field in client_type_fields:
            print(f"  - {field}")

        # Check for polymorphic_type field
        polymorphic_type_found = any(
            "polymorphicType" in field or "polymorphic_type" in field
            for field in client_type_fields
        )

        if polymorphic_type_found:
            print("\n✅ SUCCESS: polymorphic_type field found in ClientType!")
            polymorphic_field = next(
                field
                for field in client_type_fields
                if "polymorphicType" in field or "polymorphic_type" in field
            )
            print(f"   Field definition: {polymorphic_field}")
        else:
            print("\n❌ ERROR: polymorphic_type field NOT found in ClientType")
            return False

        # Also check if the field has proper type
        if "String" in polymorphic_field:
            print("✅ polymorphicType field has correct String type")
        else:
            print("⚠️  WARNING: polymorphicType field type might be incorrect")

        print("\n=== Schema Generation Test Completed ===")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_polymorphic_type_in_schema()
    sys.exit(0 if success else 1)
