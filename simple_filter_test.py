#!/usr/bin/env python3
"""
Simple test script to verify that filters work correctly for both list and paginated queries.
"""

from rail_django_graphql.schema import schema


def test_basic_filters():
    """Test basic filter functionality."""

    print("=== Testing Basic Filter Functionality ===\n")

    # Test 1: Simple paginated query with filter
    print("Test 1: Paginated query with is_approved filter")
    query = """
    query {
        comment_pages(filters: {is_approved: true}, page: 1, per_page: 5) {
            items {
                id
                content
                is_approved
            }
            page_info {
                total_count
                current_page
                has_next_page
            }
        }
    }
    """

    result = schema.execute(query)
    if result.errors:
        print(f"Error: {result.errors}")
    else:
        data = result.data["comment_pages"]
        print(f"Success: Found {len(data['items'])} approved comments")
        print(f"   Total count: {data['page_info']['total_count']}")
        print(f"   Current page: {data['page_info']['current_page']}")
        print(f"   Has next page: {data['page_info']['has_next_page']}")

    print()

    # Test 2: List query with same filter
    print("Test 2: List query with is_approved filter")
    query = """
    query {
        comments(filters: {is_approved: true}) {
            id
            content
            is_approved
        }
    }
    """

    result = schema.execute(query)
    if result.errors:
        print(f"Error: {result.errors}")
    else:
        comments = result.data["comments"]
        print(f"Success: Found {len(comments)} approved comments in list query")

    print()

    # Test 3: Text filter
    print("Test 3: Text filter with content__icontains")
    query = """
    query {
        comment_pages(filters: {content__icontains: "test"}, page: 1, per_page: 5) {
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

    result = schema.execute(query)
    if result.errors:
        print(f"Error: {result.errors}")
    else:
        data = result.data["comment_pages"]
        print(f"Success: Found {len(data['items'])} comments containing 'test'")
        print(f"   Total count: {data['page_info']['total_count']}")

    print()

    # Test 4: No filters
    print("Test 4: Paginated query without filters")
    query = """
    query {
        comment_pages(page: 1, per_page: 3) {
            items {
                id
                content
            }
            page_info {
                total_count
                current_page
            }
        }
    }
    """

    result = schema.execute(query)
    if result.errors:
        print(f"Error: {result.errors}")
    else:
        data = result.data["comment_pages"]
        print(f"Success: Found {len(data['items'])} comments (no filters)")
        print(f"   Total count: {data['page_info']['total_count']}")

    print("\n=== Filter Test Completed ===")


if __name__ == "__main__":
    test_basic_filters()
