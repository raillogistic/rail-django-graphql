#!/usr/bin/env python
"""
Debug script to test database setup and filter generation.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from test_app.models import Product, Brand, Country, Category
from rail_django_graphql.generators.filters import AdvancedFilterGenerator


def main():
    print("Testing database setup...")

    # Run migrations first
    from django.core.management import call_command

    print("Running migrations...")
    call_command("migrate", verbosity=0, interactive=False, run_syncdb=True)

    print(f"Product fields: {[f.name for f in Product._meta.get_fields()]}")
    print(f"Brand fields: {[f.name for f in Brand._meta.get_fields()]}")

    # Test data creation
    country = Country.objects.create(name="Test Country", code="TC")
    category = Category.objects.create(name="Test Category", description="Test")
    brand = Brand.objects.create(name="Test Brand", country=country, founded_year=2000)
    product = Product.objects.create(
        name="Test Product",
        price=100.00,
        category=category,
        brand=brand,
        is_active=True,
    )

    print(f"Created brand: {brand.name} from {brand.country.name}")
    print(f"Created product: {product.name}")

    # Test direct Django query
    try:
        products = Product.objects.filter(brand__country__name__icontains="Test")
        print(f"Direct Django query works: {products.count()} products found")
    except Exception as e:
        print(f"Direct Django query failed: {e}")

    # Test filter generation
    generator = AdvancedFilterGenerator(max_nested_depth=3)
    filter_set = generator.generate_filter_set(Product)
    filter_instance = filter_set()

    print(
        f'Filter has brand__country__name__icontains: {"brand__country__name__icontains" in filter_instance.filters}'
    )

    # Test filter application
    try:
        filter_data = {"brand__country__name__icontains": "Test"}
        filtered_instance = filter_set(data=filter_data, queryset=Product.objects.all())
        filtered_data = filtered_instance.qs
        print(f"Filter application works: {filtered_data.count()} products found")
    except Exception as e:
        print(f"Filter application failed: {e}")


if __name__ == "__main__":
    main()
