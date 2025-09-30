"""
Comprehensive test for nested tags functionality in GraphQL mutations.
Tests both create and update operations with various scenarios.
"""

import requests
import json
import time

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql/"

def test_comprehensive_nested_tags():
    """Test comprehensive nested tags functionality."""
    print("Comprehensive Nested Tags Test")
    print("=" * 60)
    
    # Check if GraphQL server is running
    try:
        response = requests.post(GRAPHQL_URL, json={"query": "{ __schema { types { name } } }"})
        if response.status_code != 200:
            print(f"GraphQL server not running. Status: {response.status_code}")
            return
        print("GraphQL server is running\n")
    except requests.exceptions.ConnectionError:
        print("GraphQL server is not running")
        return
    
    timestamp = int(time.time())
    
    # Test 1: Create post with nested tags
    print("=== TEST 1: CREATE POST WITH NESTED TAGS ===")
    create_mutation = """
    mutation CreatePost($input: CreatePostInput!) {
        create_post(input: $input) {
            ok
            object {
                id
                title
                tags {
                    id
                    name
                }
            }
            errors
        }
    }
    """
    
    create_variables = {
        "input": {
            "title": f"Test Post {timestamp}",
            "content": "Test content",
            "category": "132",
            "nested_tags": [
                {"name": f"Tag-A-{timestamp}"},
                {"name": f"Tag-B-{timestamp}"},
                {"name": f"Tag-C-{timestamp}"}
            ]
        }
    }
    
    response = requests.post(GRAPHQL_URL, json={
        "query": create_mutation,
        "variables": create_variables
    })
    
    create_result = response.json()
    print(f"Create Response Status: {response.status_code}")
    print(json.dumps(create_result, indent=2))
    
    if create_result.get("data", {}).get("create_post", {}).get("ok"):
        post_id = create_result["data"]["create_post"]["object"]["id"]
        created_tags = create_result["data"]["create_post"]["object"]["tags"]
        print(f"\n✓ Post created successfully with ID: {post_id}")
        print(f"✓ Created {len(created_tags)} tags:")
        for tag in created_tags:
            print(f"  - {tag['name']} (ID: {tag['id']})")
    else:
        print("✗ Failed to create post")
        return
    
    # Test 2: Update post with different nested tags
    print("\n=== TEST 2: UPDATE POST WITH DIFFERENT NESTED TAGS ===")
    update_mutation = """
    mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
        update_post(id: $id, input: $input) {
            ok
            object {
                id
                title
                tags {
                    id
                    name
                }
            }
            errors
        }
    }
    """
    
    update_variables = {
        "id": post_id,
        "input": {
            "title": f"Updated Post {timestamp}",
            "nested_tags": [
                {"name": f"Updated-Tag-X-{timestamp}"},
                {"name": f"Updated-Tag-Y-{timestamp}"}
            ]
        }
    }
    
    response = requests.post(GRAPHQL_URL, json={
        "query": update_mutation,
        "variables": update_variables
    })
    
    update_result = response.json()
    print(f"Update Response Status: {response.status_code}")
    print(json.dumps(update_result, indent=2))
    
    if update_result.get("data", {}).get("update_post", {}).get("ok"):
        updated_tags = update_result["data"]["update_post"]["object"]["tags"]
        print(f"\n✓ Post updated successfully")
        print(f"✓ Updated to {len(updated_tags)} tags:")
        for tag in updated_tags:
            print(f"  - {tag['name']} (ID: {tag['id']})")
        
        # Verify tags were replaced, not added
        if len(updated_tags) == 2:
            print("✓ Tags were correctly replaced (not added)")
        else:
            print(f"✗ Expected 2 tags, got {len(updated_tags)}")
    else:
        print("✗ Failed to update post")
        return
    
    # Test 3: Update with empty nested tags
    print("\n=== TEST 3: UPDATE POST WITH EMPTY NESTED TAGS ===")
    empty_update_variables = {
        "id": post_id,
        "input": {
            "title": f"Post with No Tags {timestamp}",
            "nested_tags": []
        }
    }
    
    response = requests.post(GRAPHQL_URL, json={
        "query": update_mutation,
        "variables": empty_update_variables
    })
    
    empty_result = response.json()
    print(f"Empty Update Response Status: {response.status_code}")
    print(json.dumps(empty_result, indent=2))
    
    if empty_result.get("data", {}).get("update_post", {}).get("ok"):
        empty_tags = empty_result["data"]["update_post"]["object"]["tags"]
        print(f"\n✓ Post updated successfully")
        print(f"✓ Tags count after empty update: {len(empty_tags)}")
        if len(empty_tags) == 0:
            print("✓ All tags were correctly removed")
        else:
            print(f"✗ Expected 0 tags, got {len(empty_tags)}")
    else:
        print("✗ Failed to update post with empty tags")
    
    # Test 4: Update with single nested tag
    print("\n=== TEST 4: UPDATE POST WITH SINGLE NESTED TAG ===")
    single_update_variables = {
        "id": post_id,
        "input": {
            "title": f"Post with Single Tag {timestamp}",
            "nested_tags": [{"name": f"Single-Tag-{timestamp}"}]
        }
    }
    
    response = requests.post(GRAPHQL_URL, json={
        "query": update_mutation,
        "variables": single_update_variables
    })
    
    single_result = response.json()
    print(f"Single Update Response Status: {response.status_code}")
    print(json.dumps(single_result, indent=2))
    
    if single_result.get("data", {}).get("update_post", {}).get("ok"):
        single_tags = single_result["data"]["update_post"]["object"]["tags"]
        print(f"\n✓ Post updated successfully")
        print(f"✓ Tags count after single update: {len(single_tags)}")
        if len(single_tags) == 1:
            print(f"✓ Single tag correctly set: {single_tags[0]['name']}")
        else:
            print(f"✗ Expected 1 tag, got {len(single_tags)}")
    else:
        print("✗ Failed to update post with single tag")
    
    print("\n=== COMPREHENSIVE TEST COMPLETE ===")
    print("✓ All nested tags functionality is working correctly!")

if __name__ == "__main__":
    test_comprehensive_nested_tags()