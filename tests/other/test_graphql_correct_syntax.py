#!/usr/bin/env python3
"""
Test GraphQL filters with correct field names and syntax.
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
from graphene.test import Client
from rail_django_graphql.schema import schema


def test_graphql_correct_syntax():
    """Test GraphQL filters with correct syntax."""

    print("=== Testing GraphQL Filters with Correct Syntax ===\n")

    # Get valid IDs from database
    users = list(User.objects.values_list("id", "username"))

    client = Client(schema)

    # Test 1: Basic paginated query without filters
    query1 = """
    query {
        comment_pages {
            items {
                id
                content
                is_approved
                author {
                    username
                }
                post {
                    title
                }
            }
            page_info {
                total_count
                current_page
            }
        }
    }
    """

    print("Test 1: Basic paginated query")
    result1 = client.execute(query1)
    if result1.get("errors"):
        print(f"  Errors: {result1['errors']}")
    else:
        data = result1["data"]["comment_pages"]
        print(f"  Success: Found {data['page_info']['total_count']} comments")
        print(f"  First comment: {data['items'][0]['content'][:50]}...")
    print()

    # Test 2: Filter by is_approved
    query2 = """
    query {
        comment_pages(is_approved: true) {
            items {
                id
                content
                is_approved
            }
            page_info {
                total_count
            }
        }
    }
    """

    print("Test 2: Filter by is_approved=true")
    result2 = client.execute(query2)
    if result2.get("errors"):
        print(f"  Errors: {result2['errors']}")
    else:
        data = result2["data"]["comment_pages"]
        print(f"  Success: Found {data['page_info']['total_count']} approved comments")
    print()

    # Test 3: Filter by content contains
    query3 = """
    query {
        comment_pages(content__icontains: "test") {
            items {
                id
                content
            }
            page_info {
                total_count
            }
        }
    }
    """

    print("Test 3: Filter by content contains 'test'")
    result3 = client.execute(query3)
    if result3.get("errors"):
        print(f"  Errors: {result3['errors']}")
    else:
        data = result3["data"]["comment_pages"]
        print(
            f"  Success: Found {data['page_info']['total_count']} comments with 'test'"
        )
    print()

    # Test 4: Filter by valid author ID
    if users:
        author_id = users[0][0]  # Get first user ID
        query4 = f"""
        query {{
            comment_pages(author: {author_id}) {{
                items {{
                    id
                    content
                    author {{
                        username
                    }}
                }}
                page_info {{
                    total_count
                }}
            }}
        }}
        """

        print(f"Test 4: Filter by author ID {author_id}")
        result4 = client.execute(query4)
        if result4.get("errors"):
            print(f"  Errors: {result4['errors']}")
        else:
            data = result4["data"]["comment_pages"]
            print(
                f"  Success: Found {data['page_info']['total_count']} comments by author"
            )
        print()

    # Test 5: Filter by valid author__in (multiple IDs)
    if len(users) >= 2:
        author_ids = [users[0][0], users[1][0]]  # Get first two user IDs
        query5 = f"""
        query {{
            comment_pages(author__in: {author_ids}) {{
                items {{
                    id
                    content
                    author {{
                        username
                    }}
                }}
                page_info {{
                    total_count
                }}
            }}
        }}
        """

        print(f"Test 5: Filter by author__in {author_ids}")
        result5 = client.execute(query5)
        if result5.get("errors"):
            print(f"  Errors: {result5['errors']}")
        else:
            data = result5["data"]["comment_pages"]
            print(
                f"  Success: Found {data['page_info']['total_count']} comments by multiple authors"
            )
        print()


if __name__ == "__main__":
    test_graphql_correct_syntax()
