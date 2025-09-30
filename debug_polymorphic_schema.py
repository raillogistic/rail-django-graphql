#!/usr/bin/env python3
"""
Debug script to find where polymorphic_ctype is appearing in the schema
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from rail_django_graphql.core.schema import SchemaBuilder


def debug_polymorphic_in_schema():
    """Debug where polymorphic_ctype appears in the schema"""
    print("Debugging polymorphic_ctype in schema...")

    try:
        # Get the schema
        builder = SchemaBuilder()
        schema = builder.get_schema()

        # Get the schema SDL
        schema_sdl = str(schema)

        # Find all occurrences of polymorphic_ctype
        lines = schema_sdl.split("\n")
        polymorphic_lines = []

        for i, line in enumerate(lines):
            if "polymorphic_ctype" in line:
                # Get context (3 lines before and after)
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = lines[start:end]
                polymorphic_lines.append(
                    {"line_number": i + 1, "line": line.strip(), "context": context}
                )

        if polymorphic_lines:
            print(
                f"\nFound {len(polymorphic_lines)} occurrences of 'polymorphic_ctype':"
            )
            for occurrence in polymorphic_lines:
                print(f"\nLine {occurrence['line_number']}: {occurrence['line']}")
                print("Context:")
                for j, context_line in enumerate(occurrence["context"]):
                    marker = " >>> " if j == 3 else "     "  # Mark the actual line
                    print(f"{marker}{context_line}")
        else:
            print("\n✅ No occurrences of 'polymorphic_ctype' found in schema!")

        # Also check for client_ptr
        client_ptr_lines = []
        for i, line in enumerate(lines):
            if "client_ptr" in line:
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = lines[start:end]
                client_ptr_lines.append(
                    {"line_number": i + 1, "line": line.strip(), "context": context}
                )

        if client_ptr_lines:
            print(f"\nFound {len(client_ptr_lines)} occurrences of 'client_ptr':")
            for occurrence in client_ptr_lines:
                print(f"\nLine {occurrence['line_number']}: {occurrence['line']}")
                print("Context:")
                for j, context_line in enumerate(occurrence["context"]):
                    marker = " >>> " if j == 3 else "     "
                    print(f"{marker}{context_line}")
        else:
            print("\n✅ No occurrences of 'client_ptr' found in schema!")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_polymorphic_in_schema()
