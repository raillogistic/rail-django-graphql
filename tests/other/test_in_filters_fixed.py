"""
Test GraphQL __in filters with corrected array syntax after fixing the schema
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from graphene.test import Client
from rail_django_graphql.schema import schema
from tests.fixtures.test_data_fixtures import (
    TestAuthor,
    TestBook,
    TestCategory,
    TestReview,
    TestPublisher,
)


def test_in_filters():
    """Test __in filters with array syntax"""

    # Rebuild schema to pick up changes
    print("Rebuilding schema...")
    from rail_django_graphql.core.schema import schema_builder

    schema_builder.rebuild_schema()

    client = Client(schema)

    # Get some valid IDs from database
    users = list(User.objects.values_list("id", flat=True)[:3])
    posts = list(Post.objects.values_list("id", flat=True)[:3])

    print(f"Testing with user IDs: {users}")
    print(f"Testing with post IDs: {posts}")

    # Test 1: Filter by multiple authors using __in
    query1 = f"""
    query {{
        comment_pages(author__in: ["57", "58", "62"]) {{
            items {{
                id
                content
                author {{
                    username
                }}
            }}
            page_info {{
                total_count
                has_next_page
                has_previous_page
            }}
        }}
    }}
    """

    print("\n=== Test 1: Filter by author__in ===")
    print(f"Query: {query1}")
    result1 = client.execute(query1)
    print(f"Result: {result1}")

    # Test 2: Filter by multiple posts using __in
    query2 = f"""
    query {{
        comment_pages(post__in: ["85", "84", "83"]) {{
            items {{
                id
                content
                post {{
                    title
                }}
            }}
            page_info {{
                total_count
                has_next_page
                has_previous_page
            }}
        }}
    }}
    """

    print("\n=== Test 2: Filter by post__in ===")
    print(f"Query: {query2}")
    result2 = client.execute(query2)
    print(f"Result: {result2}")

    # Test 3: Combine __in filter with other filters
    query3 = f"""
    query {{
        comment_pages(author__in: ["57", "58", "62"], is_approved: true) {{
            items {{
                id
                content
                is_approved
                author {{
                    username
                }}
            }}
            page_info {{
                total_count
                has_next_page
                has_previous_page
            }}
        }}
    }}
    """

    print("\n=== Test 3: Combine author__in with is_approved ===")
    print(f"Query: {query3}")
    result3 = client.execute(query3)
    print(f"Result: {result3}")


if __name__ == "__main__":
    test_in_filters()
