#!/usr/bin/env python
"""
Debug test to see exactly what's happening with error field extraction.
"""

import os
import sys
import django
import re

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import Tag
from django.db import IntegrityError


def test_database_error_parsing():
    """Test the database error parsing logic directly."""

    print("Testing database error parsing logic...")

    # Create first tag
    tag1 = Tag.objects.create(name="test_unique_debug")
    print(f"Created first tag: {tag1.name}")

    try:
        # Try to create duplicate
        tag2 = Tag.objects.create(name="test_unique_debug")
    except Exception as e:
        print(f"\nCaught exception: {type(e).__name__}")
        print(f"Exception message: {str(e)}")

        # Test the regex patterns from the mutation code
        error_message = str(e)

        # UNIQUE constraint pattern
        unique_match = re.search(
            r"UNIQUE constraint failed: (\w+)\.(\w+)", error_message
        )
        if unique_match:
            table_name = unique_match.group(1)
            field_name = unique_match.group(2)
            print(f"✅ UNIQUE constraint match found:")
            print(f"   Table: {table_name}")
            print(f"   Field: {field_name}")
        else:
            print("❌ No UNIQUE constraint match found")

        # Try alternative patterns
        alt_patterns = [
            r'duplicate key value violates unique constraint.*"(\w+)"',
            r"UNIQUE constraint failed: .*\.(\w+)",
            r"column (\w+) is not unique",
        ]

        for i, pattern in enumerate(alt_patterns):
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                print(f"✅ Alternative pattern {i+1} matched: {match.group(1)}")
            else:
                print(f"❌ Alternative pattern {i+1} no match")

    # Clean up
    Tag.objects.filter(name="test_unique_debug").delete()
    print("\nCleanup completed.")


if __name__ == "__main__":
    test_database_error_parsing()
