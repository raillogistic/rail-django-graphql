import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from tests.fixtures.test_data_fixtures import TestAuthor, TestBook, TestCategory, TestReview, TestPublisher
from django_graphql_auto.generators.filters import AdvancedFilterGenerator

# Test with Comment model specifically
generator = AdvancedFilterGenerator()
filter_class = generator.generate_filter_set(Comment)

print('Comment model fields:')
for field in Comment._meta.get_fields():
    print(f'  {field.name}: {type(field).__name__}')

print('\nGenerated filter class attributes:')
for attr_name in dir(filter_class):
    if not attr_name.startswith('_'):
        attr = getattr(filter_class, attr_name)
        print(f'  {attr_name}: {type(attr)}')

print('\nTrying to inspect Meta class:')
if hasattr(filter_class, 'Meta'):
    meta = filter_class.Meta
    print(f'  model: {getattr(meta, "model", None)}')
    print(f'  fields: {getattr(meta, "fields", None)}')
    print(f'  filter_overrides: {getattr(meta, "filter_overrides", None)}')

print('\nTrying to create instance with minimal args:')
try:
    instance = filter_class()
    print('Success with no args')
except Exception as e:
    print(f'Error with no args: {e}')

try:
    instance = filter_class(data={})
    print('Success with empty data')
except Exception as e:
    print(f'Error with empty data: {e}')

try:
    instance = filter_class(data={}, queryset=Comment.objects.none())
    print('Success with data and queryset')
    print('Base filters:')
    for name, filter_obj in instance.base_filters.items():
        print(f'  {name}: {type(filter_obj).__name__}')
except Exception as e:
    print(f'Error with data and queryset: {e}')
    import traceback
    traceback.print_exc()
