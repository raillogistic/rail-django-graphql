#!/usr/bin/env python
"""
Script to clear the GraphQL schema cache and force a rebuild.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from rail_django_graphql.core.schema import get_schema_builder


def clear_schema_cache():
    """Clear the schema cache and force a rebuild."""
    print("=== CLEARING SCHEMA CACHE ===")

    try:
        builder = get_schema_builder()
        builder.clear_schema()
        print("✅ Schema cache cleared successfully")

        # Force a rebuild by accessing the schema
        print("🔄 Forcing schema rebuild...")
        schema = builder.get_schema()
        print(
            f"✅ Schema rebuilt successfully with version: {builder.get_schema_version()}"
        )

    except Exception as e:
        print(f"❌ Error clearing schema cache: {e}")
        return False

    return True


if __name__ == "__main__":
    success = clear_schema_cache()
    sys.exit(0 if success else 1)
