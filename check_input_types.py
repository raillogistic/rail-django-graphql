# -*- coding: utf-8 -*-
from rail_django_graphql.schema import schema


def check_input_types():
    """Check the differences between CreatePostInput and UpdatePostInput"""

    # Execute introspection query for input types
    result = schema.execute("""
    {
        __schema {
            types {
                name
                kind
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
    """)

    if result.errors:
        print(f"Errors: {result.errors}")
        return

    types = result.data["__schema"]["types"]

    # Find CreatePostInput and UpdatePostInput
    create_post = next((t for t in types if t["name"] == "CreatePostInput"), None)
    update_post = next((t for t in types if t["name"] == "UpdatePostInput"), None)

    print(f"Found CreatePostInput: {create_post is not None}")
    print(f"Found UpdatePostInput: {update_post is not None}")

    if not create_post:
        print("CreatePostInput not found")
        # Let's see what Post-related input types exist
        post_inputs = [t for t in types if "Post" in t["name"] and "Input" in t["name"]]
        print("Available Post input types:")
        for t in post_inputs:
            print(f"  - {t['name']}")
        return

    if not update_post:
        print("UpdatePostInput not found")
        return

    print("=== CreatePostInput fields ===")
    create_fields = {}
    for field in create_post["inputFields"] or []:
        field_name = field["name"]
        type_name = field["type"]["name"] or (
            field["type"]["ofType"]["name"] if field["type"]["ofType"] else "Unknown"
        )
        create_fields[field_name] = type_name
        print(f"{field_name}: {type_name}")

    print("\n=== UpdatePostInput fields ===")
    update_fields = {}
    for field in update_post["inputFields"] or []:
        field_name = field["name"]
        type_name = field["type"]["name"] or (
            field["type"]["ofType"]["name"] if field["type"]["ofType"] else "Unknown"
        )
        update_fields[field_name] = type_name
        print(f"{field_name}: {type_name}")

    print("\n=== Fields only in CreatePostInput ===")
    create_only = set(create_fields.keys()) - set(update_fields.keys())
    for field in create_only:
        print(f"{field}: {create_fields[field]}")

    print("\n=== Fields only in UpdatePostInput ===")
    update_only = set(update_fields.keys()) - set(create_fields.keys())
    for field in update_only:
        print(f"{field}: {update_fields[field]}")

    print("\n=== Comment-related fields comparison ===")
    create_comment_fields = {
        k: v for k, v in create_fields.items() if "comment" in k.lower()
    }
    update_comment_fields = {
        k: v for k, v in update_fields.items() if "comment" in k.lower()
    }

    print("CreatePostInput comment fields:")
    for field, type_name in create_comment_fields.items():
        print(f"  {field}: {type_name}")

    print("UpdatePostInput comment fields:")
    for field, type_name in update_comment_fields.items():
        print(f"  {field}: {type_name}")


if __name__ == "__main__":
    check_input_types()
