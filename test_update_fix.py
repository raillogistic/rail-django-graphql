#!/usr/bin/env python
"""
Test script to verify that update mutations work correctly with partial inputs.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

import requests
import json
from test_app.models import Post, Category, Tag


def test_update_mutation():
    """Test that update mutations work with partial inputs."""

    # GraphQL endpoint
    url = "http://127.0.0.1:8000/graphql/"

    # First, let's introspect the UpdatePostInput type to see field requirements
    introspection_query = """
    query {
        __schema {
            mutationType {
                fields {
                    name
                    args {
                        name
                        type {
                            name
                            inputFields {
                                name
                                type {
                                    name
                                    ofType {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    print("=== INTROSPECTING UPDATE MUTATION ===")
    try:
        response = requests.post(url, json={"query": introspection_query})
        data = response.json()

        # Find update_post mutation
        mutations = data["data"]["__schema"]["mutationType"]["fields"]
        update_post_mutation = None

        for mutation in mutations:
            if mutation["name"] == "update_post":
                update_post_mutation = mutation
                break

        if update_post_mutation:
            print(f"Found update_post mutation")
            for arg in update_post_mutation["args"]:
                if arg["name"] == "input":
                    input_type = arg["type"]
                    print(f"Input type: {input_type['name']}")

                    if input_type["inputFields"]:
                        print("Input fields:")
                        for field in input_type["inputFields"]:
                            field_type = field["type"]
                            is_required = field_type["name"] == "NonNull"
                            actual_type = (
                                field_type["ofType"]["name"]
                                if is_required
                                else field_type["name"]
                            )
                            print(
                                f"  - {field['name']}: {actual_type} {'(required)' if is_required else '(optional)'}"
                            )
        else:
            print("update_post mutation not found")

    except Exception as e:
        print(f"Introspection failed: {e}")

    # Now test an actual update mutation
    print("\n=== TESTING PARTIAL UPDATE ===")

    # First, create a category to use
    create_category_mutation = """
    mutation {
        create_category(input: {
            name: "Test Category"
        }) {
            ok
            object {
                id
                name
            }
            errors
        }
    }
    """

    category_id = None
    try:
        response = requests.post(url, json={"query": create_category_mutation})
        category_data = response.json()

        if category_data.get("data", {}).get("create_category", {}).get("ok"):
            category_id = category_data["data"]["create_category"]["object"]["id"]
            print(f"Created category with ID: {category_id}")
        else:
            print("Failed to create category, using existing category ID 1")
            category_id = 1
    except Exception as e:
        print(f"Category creation failed: {e}, using category ID 1")
        category_id = 1

    # First, create a post to update (using integer category ID)
    create_mutation = """
    mutation {
        create_post(input: {
            title: "Test Post for Update"
            content: "Original content"
            category: 1
            is_published: false
        }) {
            ok
            object {
                id
                title
                content
                is_published
            }
            errors
        }
    }
    """

    try:
        response = requests.post(url, json={"query": create_mutation})
        create_data = response.json()

        if create_data.get("data", {}).get("create_post", {}).get("ok"):
            post_id = create_data["data"]["create_post"]["object"]["id"]
            print(f"Created post with ID: {post_id}")

            # Now try a partial update (only updating title)
            update_mutation = f"""
            mutation {{
                update_post(id: "{post_id}", input: {{
                    title: "Updated Title Only"
                }}) {{
                    ok
                    object {{
                        id
                        title
                        content
                        is_published
                    }}
                    errors
                }}
            }}
            """

            response = requests.post(url, json={"query": update_mutation})
            update_data = response.json()

            print("Update mutation response:")
            print(json.dumps(update_data, indent=2))

            if update_data.get("data", {}).get("update_post", {}).get("ok"):
                updated_post = update_data["data"]["update_post"]["object"]
                print(f"✅ Partial update successful!")
                print(f"   Title: {updated_post['title']}")
                print(f"   Content: {updated_post['content']} (should be unchanged)")
                print(
                    f"   Published: {updated_post['is_published']} (should be unchanged)"
                )
            else:
                print("❌ Partial update failed")
                errors = (
                    update_data.get("data", {}).get("update_post", {}).get("errors", [])
                )
                if errors:
                    print(f"Errors: {errors}")
        else:
            print("❌ Failed to create test post")
            print(json.dumps(create_data, indent=2))

    except Exception as e:
        print(f"Update test failed: {e}")


if __name__ == "__main__":
    test_update_mutation()
