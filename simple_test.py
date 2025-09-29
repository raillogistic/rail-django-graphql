#!/usr/bin/env python
"""
Simple test to verify subfield filtering functionality.
"""
import os
import sys
import django
from django.conf import settings
import uuid
from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')

# Setup Django
django.setup()

from tests.models import BenchmarkTestAuthor, BenchmarkTestBook, BenchmarkTestReview
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.core.settings import TypeGeneratorSettings

def test_basic_functionality():
    """Test basic subfield filtering functionality."""
    print("Testing basic subfield filtering...")
    
    try:
        # Check if we can create objects
        print("Creating test author...")
        author = BenchmarkTestAuthor.objects.create(
            nom_auteur="Test",
            prenom_auteur="Author", 
            email_auteur="test@example.com"
        )
        print(f"✓ Created author: {author}")
        
        # Generate GraphQL type
        print("Generating GraphQL type...")
        settings = TypeGeneratorSettings()
        type_generator = TypeGenerator(settings)
        author_type = type_generator.generate_object_type(BenchmarkTestAuthor)
        
        print(f"✓ Generated type: {author_type}")
        print(f"✓ Type fields: {list(author_type._meta.fields.keys())}")
        
        # Check for livres_auteur field
        if hasattr(author_type._meta, 'fields') and 'livres_auteur' in author_type._meta.fields:
            print("✓ livres_auteur field found")
            field = author_type._meta.fields['livres_auteur']
            print(f"✓ Field type: {type(field)}")
            
            # Check for filters argument
            if hasattr(field, 'args') and 'filters' in field.args:
                print("✓ Filters argument found!")
            else:
                print("✗ Filters argument not found")
        else:
            print("✗ livres_auteur field not found")
            
        # Clean up
        author.delete()
        print("✓ Test completed successfully")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_mutation():
    """Test the problematic mutation."""
    # Create test data
    user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', email='test@example.com')
    category = Category.objects.create(name='Test Category', description='Test Description')
    post = Post.objects.create(title='Test Post', content='Test Content', category=category, is_published=True)

    print(f'Created post with ID: {post.id}')

    # Test the problematic mutation
    mutation = f'''
    mutation {{
        updatePost(
            id: "{post.id}"
            input: {{
                title: "Updated Post Title"
                nested_comments: [
                    {{
                        content: "New comment"
                        author: "{user.id}"
                    }}
                ]
            }}
        ) {{
            ok
            errors
            object {{
                id
                title
                comments {{
                    id
                    content
                }}
            }}
        }}
    }}
    '''

    result = schema.execute(mutation)
    print('=== MUTATION RESULT ===')
    if result.errors:
        print(f'GraphQL Errors: {result.errors}')
    else:
        print('No GraphQL errors')
        if result.data:
            update_result = result.data.get('updatePost')
            if update_result:
                print(f'Success: {update_result.get("ok")}')
                print(f'Errors: {update_result.get("errors")}')
                if update_result.get('object'):
                    obj = update_result['object']
                    print(f'Post title: {obj.get("title")}')
                    print(f'Comments: {obj.get("comments")}')

if __name__ == "__main__":
    test_basic_functionality()
    test_mutation()