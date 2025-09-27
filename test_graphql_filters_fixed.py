#!/usr/bin/env python3
"""
Test GraphQL filters with valid data from the database.
"""

import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from tests.fixtures.test_data_fixtures import TestAuthor, TestBook, TestCategory, TestReview, TestPublisher
from django.contrib.auth.models import User
from graphene.test import Client
from django_graphql_auto.schema import schema

def test_graphql_filters():
    """Test GraphQL filters with valid data."""
    
    print("=== Testing GraphQL Filters with Valid Data ===\n")
    
    # Get valid IDs from database
    users = list(User.objects.values_list('id', 'username'))
    posts = list(Post.objects.values_list('id', 'title'))
    comments = list(Comment.objects.values_list('id', 'content', 'is_approved'))
    
    print(f"Available users: {users[:5]}...")  # Show first 5
    print(f"Available posts: {posts[:5]}...")  # Show first 5
    print(f"Available comments: {len(comments)} total")
    print(f"Approved comments: {len([c for c in comments if c[2]])}")
    print()
    
    client = Client(schema)
    
    # Test 1: Basic paginated query without filters
    query1 = """
    query {
        comment_pages {
            items {
                id
                content
                isApproved
                author {
                    username
                }
                post {
                    title
                }
            }
            pageInfo {
                totalCount
                currentPage
            }
        }
    }
    """
    
    print("Test 1: Basic paginated query")
    result1 = client.execute(query1)
    if result1.get('errors'):
        print(f"  Errors: {result1['errors']}")
    else:
        data = result1['data']['comment_pages']
        print(f"  Success: Found {data['pageInfo']['totalCount']} comments")
        print(f"  First comment: {data['items'][0]['content'][:50]}...")
    print()
    
    # Test 2: Filter by is_approved
    query2 = """
    query {
        comment_pages(isApproved: true) {
            items {
                id
                content
                isApproved
            }
            pageInfo {
                totalCount
            }
        }
    }
    """
    
    print("Test 2: Filter by is_approved=true")
    result2 = client.execute(query2)
    if result2.get('errors'):
        print(f"  Errors: {result2['errors']}")
    else:
        data = result2['data']['comment_pages']
        print(f"  Success: Found {data['pageInfo']['totalCount']} approved comments")
    print()
    
    # Test 3: Filter by content contains
    query3 = """
    query {
        comment_pages(content_Icontains: "test") {
            items {
                id
                content
            }
            pageInfo {
                totalCount
            }
        }
    }
    """
    
    print("Test 3: Filter by content contains 'test'")
    result3 = client.execute(query3)
    if result3.get('errors'):
        print(f"  Errors: {result3['errors']}")
    else:
        data = result3['data']['comment_pages']
        print(f"  Success: Found {data['pageInfo']['totalCount']} comments with 'test'")
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
                pageInfo {{
                    totalCount
                }}
            }}
        }}
        """
        
        print(f"Test 4: Filter by author ID {author_id}")
        result4 = client.execute(query4)
        if result4.get('errors'):
            print(f"  Errors: {result4['errors']}")
        else:
            data = result4['data']['comment_pages']
            print(f"  Success: Found {data['pageInfo']['totalCount']} comments by author")
        print()
    
    # Test 5: Filter by valid author__in (multiple IDs)
    if len(users) >= 2:
        author_ids = [users[0][0], users[1][0]]  # Get first two user IDs
        query5 = f"""
        query {{
            comment_pages(author_In: {author_ids}) {{
                items {{
                    id
                    content
                    author {{
                        username
                    }}
                }}
                pageInfo {{
                    totalCount
                }}
            }}
        }}
        """
        
        print(f"Test 5: Filter by author__in {author_ids}")
        result5 = client.execute(query5)
        if result5.get('errors'):
            print(f"  Errors: {result5['errors']}")
        else:
            data = result5['data']['comment_pages']
            print(f"  Success: Found {data['pageInfo']['totalCount']} comments by multiple authors")
        print()

if __name__ == '__main__':
    test_graphql_filters()
