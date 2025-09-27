#!/usr/bin/env python3
"""
Test script to verify that filters work correctly for both list and paginated queries.
"""

import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.schema import schema
from tests.fixtures.test_data_fixtures import TestReview, TestBook, TestAuthor
from django.contrib.auth.models import User as AuthUser

def test_filter_consistency():
    """Test that list and paginated queries have consistent filters."""
    
    # Create test data
    print("Creating test data...")
    
    # Create users
    user1, _ = AuthUser.objects.get_or_create(username='testuser1', defaults={'email': 'test1@example.com'})
    user2, _ = AuthUser.objects.get_or_create(username='testuser2', defaults={'email': 'test2@example.com'})
    
    # Create posts
    post1, _ = Post.objects.get_or_create(
        title='Test Post 1',
        defaults={
            'content': 'Content for test post 1',
            'author': user1,
            'slug': 'test-post-1'
        }
    )
    post2, _ = Post.objects.get_or_create(
        title='Test Post 2', 
        defaults={
            'content': 'Content for test post 2',
            'author': user2,
            'slug': 'test-post-2'
        }
    )
    
    # Create comments
    Comment.objects.filter(content__contains='Filter test').delete()  # Clean up previous tests
    
    comment1 = Comment.objects.create(
        post=post1,
        author=user1,
        content='Filter test comment 1',
        is_approved=True
    )
    comment2 = Comment.objects.create(
        post=post1,
        author=user2,
        content='Filter test comment 2',
        is_approved=False
    )
    comment3 = Comment.objects.create(
        post=post2,
        author=user1,
        content='Filter test comment 3',
        is_approved=True
    )
    
    print(f"Created {Comment.objects.filter(content__contains='Filter test').count()} test comments")
    
    # Test 1: Filter by is_approved in list query
    print("\n=== Test 1: List query with is_approved filter ===")
    list_query = """
    query {
        comments(filters: {is_approved: true}) {
            id
            content
            is_approved
        }
    }
    """
    
    result = schema.execute(list_query)
    if result.errors:
        print(f"List query errors: {result.errors}")
    else:
        approved_comments = result.data['comments']
        print(f"Found {len(approved_comments)} approved comments in list query")
        for comment in approved_comments:
            print(f"  - {comment['content']}: approved={comment['is_approved']}")
    
    # Test 2: Filter by is_approved in paginated query
    print("\n=== Test 2: Paginated query with is_approved filter ===")
    paginated_query = """
    query {
        comment_pages(filters: {is_approved: true}, page: 1, per_page: 10) {
            items {
                id
                content
                is_approved
            }
            page_info {
                total_count
                current_page
            }
        }
    }
    """
    
    result = schema.execute(paginated_query)
    if result.errors:
        print(f"Paginated query errors: {result.errors}")
    else:
        page_data = result.data['comment_pages']
        approved_comments_paginated = page_data['items']
        print(f"Found {len(approved_comments_paginated)} approved comments in paginated query")
        print(f"Total count: {page_data['page_info']['total_count']}")
        for comment in approved_comments_paginated:
            print(f"  - {comment['content']}: approved={comment['is_approved']}")
    
    # Test 3: Filter by author in list query
    print(f"\n=== Test 3: List query with author filter (user1 id: {user1.id}) ===")
    list_author_query = f"""
    query {{
        comments(filters: {{author: {user1.id}}}) {{
            id
            content
            author {{
                username
            }}
        }}
    }}
    """
    
    result = schema.execute(list_author_query)
    if result.errors:
        print(f"List author query errors: {result.errors}")
    else:
        user1_comments = result.data['comments']
        print(f"Found {len(user1_comments)} comments by user1 in list query")
        for comment in user1_comments:
            print(f"  - {comment['content']}: author={comment['author']['username']}")
    
    # Test 4: Filter by author in paginated query
    print(f"\n=== Test 4: Paginated query with author filter (user1 id: {user1.id}) ===")
    paginated_author_query = f"""
    query {{
        comment_pages(filters: {{author: {user1.id}}}, page: 1, per_page: 10) {{
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
    
    result = schema.execute(paginated_author_query)
    if result.errors:
        print(f"Paginated author query errors: {result.errors}")
    else:
        page_data = result.data['comment_pages']
        user1_comments_paginated = page_data['items']
        print(f"Found {len(user1_comments_paginated)} comments by user1 in paginated query")
        print(f"Total count: {page_data['page_info']['total_count']}")
        for comment in user1_comments_paginated:
            print(f"  - {comment['content']}: author={comment['author']['username']}")
    
    # Test 5: Filter by multiple authors using __in
    print(f"\n=== Test 5: List query with author__in filter ===")
    list_authors_in_query = f"""
    query {{
        comments(filters: {{author__in: [{user1.id}, {user2.id}]}}) {{
            id
            content
            author {{
                username
            }}
        }}
    }}
    """
    
    result = schema.execute(list_authors_in_query)
    if result.errors:
        print(f"List author__in query errors: {result.errors}")
    else:
        multi_author_comments = result.data['comments']
        print(f"Found {len(multi_author_comments)} comments by multiple authors in list query")
        for comment in multi_author_comments:
            print(f"  - {comment['content']}: author={comment['author']['username']}")
    
    # Test 6: Filter by multiple authors using __in in paginated query
    print(f"\n=== Test 6: Paginated query with author__in filter ===")
    paginated_authors_in_query = f"""
    query {{
        comment_pages(filters: {{author__in: [{user1.id}, {user2.id}]}}, page: 1, per_page: 10) {{
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
    
    result = schema.execute(paginated_authors_in_query)
    if result.errors:
        print(f"Paginated author__in query errors: {result.errors}")
    else:
        page_data = result.data['comment_pages']
        multi_author_comments_paginated = page_data['items']
        print(f"Found {len(multi_author_comments_paginated)} comments by multiple authors in paginated query")
        print(f"Total count: {page_data['page_info']['total_count']}")
        for comment in multi_author_comments_paginated:
            print(f"  - {comment['content']}: author={comment['author']['username']}")
    
    # Test 7: Text filter with icontains
    print(f"\n=== Test 7: Text filter with content__icontains ===")
    text_filter_query = """
    query {
        comments(filters: {content__icontains: "Filter test"}) {
            id
            content
        }
    }
    """
    
    result = schema.execute(text_filter_query)
    if result.errors:
        print(f"Text filter query errors: {result.errors}")
    else:
        filtered_comments = result.data['comments']
        print(f"Found {len(filtered_comments)} comments containing 'Filter test'")
        for comment in filtered_comments:
            print(f"  - {comment['content']}")
    
    # Test 8: Same text filter in paginated query
    print(f"\n=== Test 8: Paginated text filter with content__icontains ===")
    paginated_text_filter_query = """
    query {
        comment_pages(filters: {content__icontains: "Filter test"}, page: 1, per_page: 10) {
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
    
    result = schema.execute(paginated_text_filter_query)
    if result.errors:
        print(f"Paginated text filter query errors: {result.errors}")
    else:
        page_data = result.data['comment_pages']
        filtered_comments_paginated = page_data['items']
        print(f"Found {len(filtered_comments_paginated)} comments containing 'Filter test' in paginated query")
        print(f"Total count: {page_data['page_info']['total_count']}")
        for comment in filtered_comments_paginated:
            print(f"  - {comment['content']}")
    
    print("\n=== Filter consistency test completed ===")

if __name__ == '__main__':
    test_filter_consistency()
