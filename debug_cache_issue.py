#!/usr/bin/env python3
"""
Debug script to understand why the cache is not updating properly.
This will help identify the root cause of the caching issue.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.core.cache import cache
from test_app.models import Tag
from test_app.schema import invalidate_tag_cache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_cache_issue():
    """Debug the cache invalidation issue."""
    print("\n" + "=" * 80)
    print("🔍 DEBUGGING CACHE INVALIDATION ISSUE")
    print("=" * 80)

    # Clean up first
    cache.clear()
    Tag.objects.filter(name__startswith="DebugTest").delete()
    print("🧹 Environment cleaned")

    # Step 1: Check what cache backend is being used
    print("\n📋 STEP 1: Cache Backend Information")
    print(f"Cache backend: {cache.__class__.__name__}")
    print(f"Cache location: {getattr(cache, '_cache', 'N/A')}")

    # Step 2: Test basic cache operations
    print("\n📋 STEP 2: Basic Cache Operations Test")

    # Set a test cache value
    cache.set("test_key", "test_value", 300)
    cached_value = cache.get("test_key")
    print(f"✅ Cache set/get works: {cached_value == 'test_value'}")

    # Delete the test cache
    cache.delete("test_key")
    deleted_value = cache.get("test_key")
    print(f"✅ Cache delete works: {deleted_value is None}")

    # Step 3: Simulate the GraphQL caching scenario
    print("\n📋 STEP 3: GraphQL Caching Scenario Simulation")

    # Create initial tags
    tag1 = Tag.objects.create(name="DebugTestTag1", color="#FF0000")
    tag2 = Tag.objects.create(name="DebugTestTag2", color="#00FF00")
    print(f"✅ Created 2 test tags")

    # Simulate GraphQL query caching (what happens when user queries tags)
    all_tags = list(Tag.objects.filter(name__startswith="DebugTest"))
    cache_data = [{"id": t.pk, "name": t.name, "color": t.color} for t in all_tags]

    # Set various cache keys that might be used by GraphQL
    cache_keys = [
        "graphql_all_tags",
        "gql_query_tags",
        "tags_query_result",
        "graphql_tags_list",
        "query_tags_cache",
    ]

    for key in cache_keys:
        cache.set(key, cache_data, 300)

    print(f"✅ Set {len(cache_keys)} cache keys with tag data")

    # Verify cache is set
    for key in cache_keys:
        cached = cache.get(key)
        print(f"   {key}: {'✅ SET' if cached else '❌ NOT SET'}")

    # Step 4: Create a new tag and test invalidation
    print("\n📋 STEP 4: Create New Tag and Test Invalidation")

    new_tag = Tag.objects.create(name="DebugTestNewTag", color="#0000FF")
    print(f"✅ Created new tag: {new_tag.name} (ID: {new_tag.pk})")

    # Call our invalidation function
    print("🔄 Calling invalidate_tag_cache...")
    invalidate_tag_cache(new_tag)

    # Check if cache was invalidated
    print("\n📋 STEP 5: Check Cache Invalidation Results")

    invalidated_count = 0
    for key in cache_keys:
        cached = cache.get(key)
        if cached is None:
            print(f"   {key}: ✅ INVALIDATED")
            invalidated_count += 1
        else:
            print(f"   {key}: ❌ STILL CACHED")

    print(
        f"\n📊 Invalidation Results: {invalidated_count}/{len(cache_keys)} keys invalidated"
    )

    # Step 6: Test what happens with a fresh query
    print("\n📋 STEP 6: Fresh Query Test")

    # Simulate what happens when GraphQL makes a fresh query
    fresh_tags = list(Tag.objects.filter(name__startswith="DebugTest"))
    print(f"✅ Fresh query returns {len(fresh_tags)} tags")

    # Check if new tag is included
    new_tag_found = any(tag.name == "DebugTestNewTag" for tag in fresh_tags)
    print(f"✅ New tag found in fresh query: {new_tag_found}")

    # Step 7: Test the actual GraphQL caching mechanism
    print("\n📋 STEP 7: GraphQL Caching Mechanism Test")

    try:
        from rail_django_graphql.extensions.caching import get_cache_manager

        cache_manager = get_cache_manager()
        print(f"✅ Cache manager available: {cache_manager.__class__.__name__}")

        # Test cache manager methods
        if hasattr(cache_manager, "get"):
            print("✅ Cache manager has 'get' method")
        if hasattr(cache_manager, "set"):
            print("✅ Cache manager has 'set' method")
        if hasattr(cache_manager, "delete"):
            print("✅ Cache manager has 'delete' method")
        if hasattr(cache_manager, "invalidate_pattern"):
            print("✅ Cache manager has 'invalidate_pattern' method")
        else:
            print("❌ Cache manager missing 'invalidate_pattern' method")
        if hasattr(cache_manager, "invalidate_model"):
            print("✅ Cache manager has 'invalidate_model' method")
        else:
            print("❌ Cache manager missing 'invalidate_model' method")

    except Exception as e:
        print(f"❌ Error with cache manager: {e}")

    # Step 8: Check Django cache settings
    print("\n📋 STEP 8: Django Cache Settings")

    try:
        from django.conf import settings

        cache_config = getattr(settings, "CACHES", {})
        print(f"Cache configuration: {cache_config}")

        # Check if there are multiple cache configurations
        if "default" in cache_config:
            default_cache = cache_config["default"]
            print(f"Default cache backend: {default_cache.get('BACKEND', 'Unknown')}")
            print(f"Default cache location: {default_cache.get('LOCATION', 'Unknown')}")

    except Exception as e:
        print(f"❌ Error reading cache settings: {e}")

    # Step 9: Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)

    if invalidated_count == len(cache_keys):
        print("✅ Cache invalidation is working correctly!")
        print("🔍 The issue might be:")
        print("   1. GraphQL is using different cache keys than we're invalidating")
        print("   2. The caching happens at a different level (query result caching)")
        print("   3. Browser or client-side caching")
        print("   4. GraphQL introspection cache")
    else:
        print("❌ Cache invalidation is not working properly!")
        print("🔧 Possible solutions:")
        print("   1. Check if cache backend supports the operations we're using")
        print("   2. Verify cache key naming conventions")
        print("   3. Use cache.clear() as a more aggressive approach")
        print("   4. Check Django cache middleware configuration")

    print("\n🚀 Next Steps:")
    print(
        "1. Check the actual GraphQL query execution and see what cache keys are used"
    )
    print("2. Add more logging to see exactly what's being cached and when")
    print("3. Try using cache.clear() instead of selective invalidation")
    print("4. Check if there's client-side caching in GraphiQL")

    # Cleanup
    Tag.objects.filter(name__startswith="DebugTest").delete()
    cache.clear()
    print("\n🧹 Cleanup completed")


if __name__ == "__main__":
    debug_cache_issue()
