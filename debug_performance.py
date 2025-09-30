import os
import sys
import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from tests.test_nested_field_filtering import Product
from rail_django_graphql.generators.filters import AdvancedFilterGenerator

generator = AdvancedFilterGenerator()

test_filters = {
    "name__icontains": "test",
    "category__name__exact": "Electronics",
    "brand__country__name__icontains": "USA",
    "brand__founded_year__gte": 2000,
    "is_active": True,
}

print("Test filters:")
for filter_name, filter_value in test_filters.items():
    has_double_underscore = "__" in filter_name
    print(f"  {filter_name}: {filter_value} (has __: {has_double_underscore})")

analysis = generator.analyze_query_performance(Product, test_filters)
print(f"\nAnalysis results:")
print(f'  Total filters: {analysis["total_filters"]}')
print(f'  Nested filters: {analysis["nested_filters"]}')
print(f'  Max depth: {analysis["max_depth"]}')
