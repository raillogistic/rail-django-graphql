#!/usr/bin/env python3
"""
Test ModelMultipleChoiceFilter choices and validation.
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
from django.contrib.auth.models import User
from rail_django_graphql.generators.filters import AdvancedFilterGenerator


def test_filter_choices():
    """Test ModelMultipleChoiceFilter choices."""

    print("=== Testing Filter Choices ===\n")

    # Create filter generator
    filter_gen = AdvancedFilterGenerator()

    # Generate filter class for Comment model
    filter_class = filter_gen.generate_filter_set(Comment)

    # Create an instance to inspect the filters
    filterset = filter_class({}, Comment.objects.all())

    # Check the author__in filter
    author_in_filter = filterset.filters.get("author__in")
    if author_in_filter:
        print(f"author__in filter: {author_in_filter}")
        print(f"author__in queryset: {author_in_filter.queryset}")
        print(f"author__in queryset count: {author_in_filter.queryset.count()}")
        print(
            f"author__in choices: {list(author_in_filter.queryset.values_list('id', 'username'))}"
        )
        print()

    # Check the post__in filter
    post_in_filter = filterset.filters.get("post__in")
    if post_in_filter:
        print(f"post__in filter: {post_in_filter}")
        print(f"post__in queryset: {post_in_filter.queryset}")
        print(f"post__in queryset count: {post_in_filter.queryset.count()}")
        print(
            f"post__in choices: {list(post_in_filter.queryset.values_list('id', 'title'))}"
        )
        print()

    # Test with valid choices
    print("Testing with valid choices:")

    # Get valid user IDs
    user_ids = list(User.objects.values_list("id", flat=True))[:2]
    print(f"Valid user IDs: {user_ids}")

    # Get valid post IDs
    post_ids = list(Post.objects.values_list("id", flat=True))[:2]
    print(f"Valid post IDs: {post_ids}")

    # Test with valid data
    test_data = {
        "author__in": user_ids,
        "post__in": post_ids,
    }

    filterset = filter_class(test_data, Comment.objects.all())
    print(f"FilterSet with valid data is_valid(): {filterset.is_valid()}")
    if not filterset.is_valid():
        print(f"Errors: {filterset.errors}")
    else:
        print(f"Filtered queryset count: {filterset.qs.count()}")


if __name__ == "__main__":
    test_filter_choices()
