#!/usr/bin/env python3
"""
Debug script to test filterset validation and understand filter failures.
"""

import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from tests.fixtures.test_data_fixtures import (
    TestAuthor,
    TestBook,
    TestCategory,
    TestReview,
    TestPublisher,
)
from rail_django_graphql.generators.filters import AdvancedFilterGenerator


def debug_filterset_validation():
    """Debug filterset validation issues."""

    print("=== Debugging FilterSet Validation ===\n")

    # Create filter generator
    filter_gen = AdvancedFilterGenerator()

    # Generate filter class for Comment model
    filter_class = filter_gen.generate_filter_set(Comment)
    print(f"Generated filter class: {filter_class}")
    print(f"Filter class MRO: {filter_class.__mro__}")

    # Test different filter scenarios
    test_cases = [
        {"is_approved": True},
        {"is_approved": "true"},  # String instead of boolean
        {"content__icontains": "test"},
        {"author": 1},
        {"author": "1"},  # String instead of int
        {"nonexistent_field": "value"},  # Invalid field
        {"author__in": [1, 2]},
        {"post__in": [1, 2]},
    ]

    queryset = Comment.objects.all()
    print(f"Base queryset count: {queryset.count()}\n")

    for i, filters in enumerate(test_cases, 1):
        print(f"Test {i}: {filters}")

        try:
            # Create filterset
            filterset = filter_class(filters, queryset)
            print(f"  FilterSet created successfully")
            print(f"  FilterSet data: {filterset.data}")
            print(f"  FilterSet is_valid(): {filterset.is_valid()}")

            if not filterset.is_valid():
                print(f"  FilterSet errors: {filterset.errors}")
                print(
                    f"  FilterSet form errors: {filterset.form.errors if hasattr(filterset, 'form') else 'No form'}"
                )
            else:
                try:
                    qs = filterset.qs
                    print(f"  Filtered queryset count: {qs.count()}")
                except Exception as e:
                    print(f"  Error accessing qs: {e}")

        except Exception as e:
            print(f"  Error creating FilterSet: {e}")
            import traceback

            traceback.print_exc()

        print()


if __name__ == "__main__":
    debug_filterset_validation()
