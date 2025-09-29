import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Tag, Category
from django_graphql_auto.schema import schema

def main():
    print("=== SIMPLE NESTED TAGS TEST ===")
    
    # Clean up
    Tag.objects.filter(name="test_tag").delete()
    Post.objects.filter(title="Test Post").delete()
    User.objects.filter(username="test_user").delete()
    Category.objects.filter(name="Test Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_user', email='test@test.com')
    category = Category.objects.create(name='Test Category')
    post = Post.objects.create(title='Test Post', content='Test content', category=category)
    
    print(f"Created post: {post.title} (ID: {post.id})")
    
    # Test nested tags
    mutation = f'''
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_tags:[{{name:"test_tag"}}] 
            title:"Updated Post", 
        }}){{ 
            ok 
            object{{ 
                title
                tags{{ 
                    name 
                }} 
            }} 
            errors 
        }} 
    }}
    '''
    
    print("Executing mutation...")
    result = schema.execute(mutation)
    
    if result.errors:
        print(f"GraphQL errors: {result.errors}")
        return
    
    data = result.data['update_post']
    print(f"Result: {data}")
    
    if data['ok']:
        print(f"Title: {data['object']['title']}")
        print(f"Tags: {data['object']['tags']}")
        
        # Check database
        post.refresh_from_db()
        print(f"DB tags: {list(post.tags.all())}")
        
        tag_exists = Tag.objects.filter(name="test_tag").exists()
        print(f"Tag exists: {tag_exists}")
    else:
        print(f"Failed: {data['errors']}")

if __name__ == "__main__":
    main()