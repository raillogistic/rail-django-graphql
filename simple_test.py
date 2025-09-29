#!/usr/bin/env python
"""
Simple test to verify subfield filtering functionality.
"""
import os
import sys
import django
from django.conf import settings

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

if __name__ == "__main__":
    test_basic_functionality()