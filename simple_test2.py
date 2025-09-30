print("Starting test...")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

print("Django setup complete")

from test_app.models import Tag

print("Model imported")

# Create and test
tag = Tag.objects.create(name="simple_test")
print(f"Created tag: {tag.name}")

# Clean up
tag.delete()
print("Test completed")
