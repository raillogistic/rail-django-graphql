#!/usr/bin/env python
"""
Debug script to examine the input type generation for update mutations.
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

from test_app.models import Post
from rail_django_graphql.generators.types import TypeGenerator


def debug_input_type():
    """Debug the input type generation for Post updates."""

    type_generator = TypeGenerator()

    print("=== DEBUGGING POST INPUT TYPE GENERATION ===")

    # Generate input type for create
    print("\n1. CREATE INPUT TYPE:")
    create_input_type = type_generator.generate_input_type(
        Post, partial=False, mutation_type="create"
    )
    print(f"Class name: {create_input_type.__name__}")

    if hasattr(create_input_type, "_meta") and hasattr(
        create_input_type._meta, "fields"
    ):
        print("Fields:")
        for field_name, field in create_input_type._meta.fields.items():
            is_required = hasattr(field, "type") and hasattr(field.type, "of_type")
            print(
                f"  - {field_name}: {field.type} {'(required)' if is_required else '(optional)'}"
            )

    # Generate input type for update
    print("\n2. UPDATE INPUT TYPE:")
    update_input_type = type_generator.generate_input_type(
        Post, partial=True, mutation_type="update"
    )
    print(f"Class name: {update_input_type.__name__}")

    if hasattr(update_input_type, "_meta") and hasattr(
        update_input_type._meta, "fields"
    ):
        print("Fields:")
        for field_name, field in update_input_type._meta.fields.items():
            is_required = hasattr(field, "type") and hasattr(field.type, "of_type")
            print(
                f"  - {field_name}: {field.type} {'(required)' if is_required else '(optional)'}"
            )

    # Check if they're the same object (caching issue)
    print(f"\n3. SAME OBJECT? {create_input_type is update_input_type}")

    # Check the registry
    print(f"\n4. REGISTRY CONTENTS:")
    for key, value in type_generator._input_type_registry.items():
        print(f"  - {key}: {value.__name__}")


if __name__ == "__main__":
    debug_input_type()
