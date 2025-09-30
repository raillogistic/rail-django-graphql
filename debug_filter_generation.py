import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from django.core.management import call_command
from test_app.models import Product, Brand, Category, Country
from rail_django_graphql.generators.filters import AdvancedFilterGenerator


def main():
    # Run migrations to ensure tables exist
    call_command("migrate", verbosity=0)

    # Create test data
    country = Country.objects.create(name="États-Unis", code="US")
    brand = Brand.objects.create(name="TechCorp", country=country, founded_year=2000)
    category = Category.objects.create(
        name="Electronics", description="Electronic devices"
    )
    product = Product.objects.create(
        name="Smartphone Pro", brand=brand, category=category, price=999.99
    )

    print(f"Created test data:")
    print(f"  Country: {country}")
    print(f"  Brand: {brand}")
    print(f"  Product: {product}")

    # Test direct Django query
    print(f"\nDirect Django query works:")
    products = Product.objects.filter(brand__country__name__icontains="États")
    print(f"  Found {products.count()} products")

    # Generate filters using AdvancedFilterGenerator
    generator = AdvancedFilterGenerator(max_nested_depth=3, enable_nested_filters=True)
    filter_set = generator.generate_filter_set(Product)

    print(f"\nGenerated filters:")
    filter_instance = filter_set()
    for filter_name in sorted(filter_instance.filters.keys()):
        if "country" in filter_name:
            print(f"  {filter_name}: {filter_instance.filters[filter_name]}")
            # Check the actual field_name attribute of the filter
            filter_obj = filter_instance.filters[filter_name]
            if hasattr(filter_obj, "field_name"):
                print(f"    -> field_name: {filter_obj.field_name}")

    # Try to apply the filter using the correct FilterSet API
    print(f"\nTrying to apply filter brand__country__name__icontains:")
    try:
        # Use the FilterSet with data parameter
        filter_instance_with_data = filter_set(
            data={"brand__country__name__icontains": "États"},
            queryset=Product.objects.all(),
        )
        filtered_queryset = filter_instance_with_data.qs
        print(f"  Success: Found {filtered_queryset.count()} products")
        for product in filtered_queryset:
            print(
                f"    - {product.name} (Brand: {product.brand.name}, Country: {product.brand.country.name})"
            )
    except Exception as e:
        print(f"  Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
