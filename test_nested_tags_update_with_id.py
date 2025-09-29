import requests
import json
import time

# GraphQL endpoint
url = "http://localhost:8000/graphql/"

# Test updating nested tags with id and name
def test_nested_tags_update_with_id():
    print("Testing nested tags update with id and name...")
    
    # Use timestamp to ensure unique tag names
    timestamp = int(time.time())
    
    # First, create a post with some tags
    create_mutation = """
    mutation CreatePost($input: CreatePostInput!) {
        create_post(input: $input) {
            ok
            object {
                id
                title
                content
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
            "title": f"Test Post for ID Update {timestamp}",
            "content": "Testing nested tags update with ID",
            "category": "132",
            "nested_tags": [
                {"name": f"Original Tag 1 {timestamp}"},
                {"name": f"Original Tag 2 {timestamp}"}
            ]
        }
    }
    
    # Create the post
    response = requests.post(url, json={
        "query": create_mutation,
        "variables": create_variables
    })
    
    create_result = response.json()
    print("Create Response:", json.dumps(create_result, indent=2))
    
    if "errors" in create_result:
        print("Error in create mutation:", create_result["errors"])
        return
    
    if not create_result["data"]["create_post"]["ok"]:
        print("Create mutation failed:", create_result["data"]["create_post"]["errors"])
        return
    
    post_id = create_result["data"]["create_post"]["object"]["id"]
    original_tags = create_result["data"]["create_post"]["object"]["tags"]
    
    print(f"Created post with ID: {post_id}")
    print(f"Original tags: {original_tags}")
    
    # Get the ID of the first tag to update
    tag_id_to_update = original_tags[0]["id"]
    print(f"Tag ID to update: {tag_id_to_update}")
    
    # Now update the post, modifying the first tag's name using its ID
    update_mutation = """
    mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
        update_post(id: $id, input: $input) {
            ok
            object {
                id
                title
                content
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
            "nested_tags": [
                {"name": f"Updated Tag Name {timestamp}", "id": tag_id_to_update},
                {"name": f"New Tag {timestamp}"}
            ]
        }
    }
    
    # Update the post
    response = requests.post(url, json={
        "query": update_mutation,
        "variables": update_variables
    })
    
    update_result = response.json()
    print("Update Response:", json.dumps(update_result, indent=2))
    
    if "errors" in update_result:
        print("Error in update mutation:", update_result["errors"])
        return
    
    if not update_result["data"]["update_post"]["ok"]:
        print("Update mutation failed:", update_result["data"]["update_post"]["errors"])
        return
    
    updated_tags = update_result["data"]["update_post"]["object"]["tags"]
    print(f"Updated tags: {updated_tags}")
    
    # Verify the tag was updated
    updated_tag = next((tag for tag in updated_tags if tag["id"] == tag_id_to_update), None)
    if updated_tag:
        print(f"Tag with ID {tag_id_to_update} was updated to: {updated_tag['name']}")
        if updated_tag["name"] == f"Updated Tag Name {timestamp}":
            print("✅ SUCCESS: Tag was updated correctly!")
        else:
            print("❌ FAILURE: Tag name was not updated correctly")
    else:
        print(f"❌ FAILURE: Tag with ID {tag_id_to_update} not found in updated tags")

if __name__ == "__main__":
    test_nested_tags_update_with_id()