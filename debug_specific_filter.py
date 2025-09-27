import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from tests.fixtures.test_data_fixtures import TestAuthor, TestBook, TestCategory, TestReview, TestPublisher
from django_graphql_auto.generators.filters import AdvancedFilterGenerator

# Test with Comment model specifically
generator = AdvancedFilterGenerator()
filter_class = generator.generate_filter_set(Comment)

print('Testing specific filter instantiation:')

# Test the problematic filter that requires queryset
instance = filter_class(data={}, queryset=Comment.objects.none())
print('FilterSet created successfully')

# Check which filters might need queryset
for name, filter_obj in instance.base_filters.items():
    print(f'{name}: {type(filter_obj).__name__}')
    if hasattr(filter_obj, 'queryset'):
        print(f'  - Has queryset attribute: {filter_obj.queryset}')
    if 'ModelMultipleChoiceFilter' in type(filter_obj).__name__:
        print(f'  - ModelMultipleChoiceFilter detected!')

# Now test the actual GraphQL query execution
print('\nTesting GraphQL query execution:')
from graphene import Schema
from test_app.schema import Query

schema = Schema(query=Query)

query = '''
query {
  comment_pages(page: 1, per_page: 5, is_approved: true, order_by: ["-created_at"]) {
    items {
      id
      content
      is_approved
      created_at
    }
    page_info {
      has_next_page
      has_previous_page
      total_pages
      total_items
    }
  }
}
'''

try:
    result = schema.execute(query)
    if result.errors:
        print('GraphQL Errors:')
        for error in result.errors:
            print(f'  - {error}')
    else:
        print('GraphQL Query executed successfully!')
        print(f'Data: {result.data}')
except Exception as e:
    print(f'Exception during GraphQL execution: {e}')
    import traceback
    traceback.print_exc()
