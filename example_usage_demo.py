"""
Practical Demo: Using Auto-Generated GraphQL Schema

This script demonstrates how to interact with the auto-generated GraphQL schema
using actual queries and mutations. It shows the generated schema in action.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_app.settings')
    django.setup()

from graphql import build_client_schema, get_introspection_query, graphql_sync
from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.core.settings import SchemaSettings, MutationGeneratorSettings
from test_app.models import Category, Tag, Post, Comment
from django.contrib.auth.models import User


def create_demo_schema():
    """Create a demo schema for testing."""
    schema_settings = SchemaSettings(
        excluded_apps=["admin", "auth", "contenttypes", "sessions"],
        enable_introspection=True,
        enable_graphiql=True,
    )
    
    mutation_settings = MutationGeneratorSettings(
        generate_create=True,
        generate_update=True,
        generate_delete=True,
        enable_method_mutations=True,
    )
    
    schema_builder = SchemaBuilder(schema_settings)
    schema_builder.mutation_generator.settings = mutation_settings
    
    return schema_builder.get_schema()


def demo_introspection(schema):
    """Demonstrate schema introspection to see what was auto-generated."""
    print("=" * 60)
    print("SCHEMA INTROSPECTION DEMO")
    print("=" * 60)
    
    # Get introspection query
    introspection_query = get_introspection_query()
    
    # Execute introspection
    result = graphql_sync(schema, {"query": introspection_query})
    
    if result.errors:
        print("Introspection errors:", result.errors)
        return
    
    # Parse the schema
    schema_dict = result.data
    types = schema_dict['__schema']['types']
    
    # Show auto-generated types
    print("\n📋 AUTO-GENERATED TYPES:")
    model_types = [t for t in types if t['name'].endswith('Type') and not t['name'].startswith('__')]
    for type_info in model_types:
        print(f"  • {type_info['name']}")
        if type_info['fields']:
            for field in type_info['fields'][:5]:  # Show first 5 fields
                print(f"    - {field['name']}: {field['type']['name'] or field['type']['ofType']['name']}")
            if len(type_info['fields']) > 5:
                print(f"    ... and {len(type_info['fields']) - 5} more fields")
    
    # Show queries
    query_type = next((t for t in types if t['name'] == 'Query'), None)
    if query_type and query_type['fields']:
        print(f"\n🔍 AUTO-GENERATED QUERIES ({len(query_type['fields'])}):")
        for field in query_type['fields'][:10]:  # Show first 10 queries
            print(f"  • {field['name']}")
    
    # Show mutations
    mutation_type = next((t for t in types if t['name'] == 'Mutation'), None)
    if mutation_type and mutation_type['fields']:
        print(f"\n✏️ AUTO-GENERATED MUTATIONS ({len(mutation_type['fields'])}):")
        for field in mutation_type['fields'][:10]:  # Show first 10 mutations
            print(f"  • {field['name']}")


def demo_queries(schema):
    """Demonstrate various auto-generated queries."""
    print("\n" + "=" * 60)
    print("QUERY EXAMPLES DEMO")
    print("=" * 60)
    
    # Create some test data first
    setup_test_data()
    
    # Example 1: List all categories
    print("\n📋 Query 1: List all categories")
    query1 = """
    query {
        allCategories {
            edges {
                node {
                    id
                    name
                    description
                    isActive
                    createdAt
                    postCount
                }
            }
        }
    }
    """
    
    result1 = graphql_sync(schema, {"query": query1})
    if result1.errors:
        print("Query 1 errors:", result1.errors)
    else:
        categories = result1.data['allCategories']['edges']
        print(f"Found {len(categories)} categories:")
        for edge in categories:
            cat = edge['node']
            print(f"  • {cat['name']}: {cat['description'][:50]}...")
    
    # Example 2: Get a specific post with relationships
    print("\n📋 Query 2: Get post with category and tags")
    query2 = """
    query {
        allPosts(first: 1) {
            edges {
                node {
                    id
                    title
                    content
                    isPublished
                    createdAt
                    category {
                        name
                    }
                    tags {
                        edges {
                            node {
                                name
                                color
                            }
                        }
                    }
                    titleWithCategory
                    wordCount
                }
            }
        }
    }
    """
    
    result2 = graphql_sync(schema, {"query": query2})
    if result2.errors:
        print("Query 2 errors:", result2.errors)
    else:
        posts = result2.data['allPosts']['edges']
        if posts:
            post = posts[0]['node']
            print(f"Post: {post['title']}")
            print(f"Category: {post['category']['name']}")
            print(f"Word count: {post['wordCount']}")
            print(f"Tags: {[tag['node']['name'] for tag in post['tags']['edges']]}")
    
    # Example 3: Filtered query
    print("\n📋 Query 3: Filter posts by category")
    query3 = """
    query {
        allPosts(category_Name_Icontains: "Tech") {
            edges {
                node {
                    title
                    category {
                        name
                    }
                }
            }
        }
    }
    """
    
    result3 = graphql_sync(schema, {"query": query3})
    if result3.errors:
        print("Query 3 errors:", result3.errors)
    else:
        filtered_posts = result3.data['allPosts']['edges']
        print(f"Found {len(filtered_posts)} posts in Tech category")


def demo_mutations(schema):
    """Demonstrate auto-generated mutations."""
    print("\n" + "=" * 60)
    print("MUTATION EXAMPLES DEMO")
    print("=" * 60)
    
    # Example 1: Create a new category
    print("\n✏️ Mutation 1: Create new category")
    mutation1 = """
    mutation {
        createCategory(input: {
            name: "Science"
            description: "Articles about science and research"
            isActive: true
        }) {
            category {
                id
                name
                description
                isActive
            }
            success
            errors
        }
    }
    """
    
    result1 = graphql_sync(schema, {"query": mutation1})
    if result1.errors:
        print("Mutation 1 errors:", result1.errors)
    else:
        create_result = result1.data['createCategory']
        if create_result['success']:
            cat = create_result['category']
            print(f"✅ Created category: {cat['name']} (ID: {cat['id']})")
        else:
            print(f"❌ Failed to create category: {create_result['errors']}")
    
    # Example 2: Update existing category
    print("\n✏️ Mutation 2: Update category")
    mutation2 = """
    mutation {
        updateCategory(id: "1", input: {
            description: "Updated description for technology category"
        }) {
            category {
                id
                name
                description
            }
            success
            errors
        }
    }
    """
    
    result2 = graphql_sync(schema, {"query": mutation2})
    if result2.errors:
        print("Mutation 2 errors:", result2.errors)
    else:
        update_result = result2.data['updateCategory']
        if update_result['success']:
            cat = update_result['category']
            print(f"✅ Updated category: {cat['name']}")
            print(f"   New description: {cat['description']}")
        else:
            print(f"❌ Failed to update category: {update_result['errors']}")


def demo_custom_mutations(schema):
    """Demonstrate custom model method mutations."""
    print("\n" + "=" * 60)
    print("CUSTOM METHOD MUTATIONS DEMO")
    print("=" * 60)
    
    # Example 1: Activate category (custom method)
    print("\n🔧 Custom Mutation 1: Activate category")
    mutation1 = """
    mutation {
        activateCategory(id: "1") {
            success
            result
            errors
        }
    }
    """
    
    result1 = graphql_sync(schema, {"query": mutation1})
    if result1.errors:
        print("Custom mutation 1 errors:", result1.errors)
    else:
        activate_result = result1.data['activateCategory']
        if activate_result['success']:
            print(f"✅ Category activated: {activate_result['result']}")
        else:
            print(f"❌ Failed to activate category: {activate_result['errors']}")
    
    # Example 2: Publish post (business logic method)
    print("\n🔧 Custom Mutation 2: Publish post")
    mutation2 = """
    mutation {
        publishPost(id: "1", publishNotes: "Ready for publication") {
            success
            result
            errors
        }
    }
    """
    
    result2 = graphql_sync(schema, {"query": mutation2})
    if result2.errors:
        print("Custom mutation 2 errors:", result2.errors)
    else:
        publish_result = result2.data['publishPost']
        if publish_result['success']:
            print(f"✅ Post published: {publish_result['result']}")
        else:
            print(f"❌ Failed to publish post: {publish_result['errors']}")


def setup_test_data():
    """Create some test data for the demo."""
    # Create categories
    tech_cat, _ = Category.objects.get_or_create(
        name="Technology",
        defaults={
            "description": "Articles about technology and programming",
            "is_active": True
        }
    )
    
    science_cat, _ = Category.objects.get_or_create(
        name="Science",
        defaults={
            "description": "Articles about science and research",
            "is_active": True
        }
    )
    
    # Create tags
    python_tag, _ = Tag.objects.get_or_create(
        name="Python",
        defaults={"color": "#3776ab"}
    )
    
    django_tag, _ = Tag.objects.get_or_create(
        name="Django",
        defaults={"color": "#092e20"}
    )
    
    # Create a user for posts
    user, _ = User.objects.get_or_create(
        username="demo_user",
        defaults={
            "email": "demo@example.com",
            "first_name": "Demo",
            "last_name": "User"
        }
    )
    
    # Create posts
    post1, _ = Post.objects.get_or_create(
        title="Introduction to Django GraphQL",
        defaults={
            "content": "This is a comprehensive guide to using GraphQL with Django. " * 20,
            "category": tech_cat,
            "is_published": True
        }
    )
    post1.tags.add(python_tag, django_tag)
    
    post2, _ = Post.objects.get_or_create(
        title="Advanced Python Techniques",
        defaults={
            "content": "Learn advanced Python programming techniques and best practices. " * 15,
            "category": tech_cat,
            "is_published": False
        }
    )
    post2.tags.add(python_tag)
    
    print("✅ Test data created successfully!")


def main():
    """Run the complete demo."""
    print("🚀 DJANGO GRAPHQL AUTO-GENERATION DEMO")
    print("=" * 60)
    print("This demo shows how the library automatically generates")
    print("GraphQL schema from your Django models.")
    
    # Create the schema
    print("\n📦 Creating auto-generated schema...")
    schema = create_demo_schema()
    print("✅ Schema created successfully!")
    
    # Run demos
    demo_introspection(schema)
    demo_queries(schema)
    demo_mutations(schema)
    demo_custom_mutations(schema)
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETED!")
    print("=" * 60)
    print("\nKey Features Demonstrated:")
    print("✅ Automatic type generation from Django models")
    print("✅ Auto-generated CRUD queries and mutations")
    print("✅ Relationship handling (ForeignKey, ManyToMany)")
    print("✅ Property fields (@property methods)")
    print("✅ Custom method mutations (@mutation, @business_logic)")
    print("✅ Filtering and pagination support")
    print("✅ Schema introspection")
    
    print("\n📚 Next Steps:")
    print("• Check the generated schema.graphql file")
    print("• Use GraphiQL interface for interactive testing")
    print("• Customize settings for your specific needs")
    print("• Add authentication and permissions")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()