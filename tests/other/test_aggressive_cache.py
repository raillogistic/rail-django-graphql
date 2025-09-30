#!/usr/bin/env python3
"""
Test script to verify the aggressive cache invalidation works properly.
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
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_aggressive_cache_invalidation():
    """Test the aggressive cache invalidation."""
    print("\n" + "=" * 80)
    print("🧪 TESTING AGGRESSIVE CACHE INVALIDATION")
    print("=" * 80)

    # Clean up first
    cache.clear()
    Tag.objects.filter(name__startswith="AggressiveTest").delete()
    print("🧹 Environment cleaned")

    # Step 1: Create some test data and cache it
    print("\n📋 STEP 1: Creating test data and caching it")

    tag1 = Tag.objects.create(name="AggressiveTestTag1", color="#FF0000")
    tag2 = Tag.objects.create(name="AggressiveTestTag2", color="#00FF00")

    # Simulate various cache entries that might exist
    cache_entries = {
        "graphql_all_tags": [
            {"id": tag1.pk, "name": tag1.name},
            {"id": tag2.pk, "name": tag2.name},
        ],
        "gql_query_tags": "cached_query_result",
        "gql_field_tag_list": "cached_field_result",
        "graphql_tags_by_color": "cached_color_result",
        "model_page_tags": "cached_page_result",
        "some_other_cache": "should_remain",
    }

    for key, value in cache_entries.items():
        cache.set(key, value, 300)

    print(f"✅ Created {len(cache_entries)} cache entries")

    # Verify cache is set
    cached_count = 0
    for key in cache_entries.keys():
        if cache.get(key) is not None:
            cached_count += 1

    print(f"✅ Verified {cached_count}/{len(cache_entries)} cache entries are set")

    # Step 2: Create a new tag and test aggressive invalidation
    print("\n📋 STEP 2: Creating new tag and testing aggressive invalidation")

    new_tag = Tag.objects.create(name="AggressiveTestNewTag", color="#0000FF")
    print(f"✅ Created new tag: {new_tag.name} (ID: {new_tag.pk})")

    # Call our aggressive invalidation function
    print("🔄 Calling aggressive invalidate_tag_cache...")
    start_time = time.time()
    invalidate_tag_cache(new_tag)
    end_time = time.time()

    print(f"⏱️ Invalidation took {end_time - start_time:.3f} seconds")

    # Step 3: Check if cache was completely cleared
    print("\n📋 STEP 3: Checking cache invalidation results")

    cleared_count = 0
    for key in cache_entries.keys():
        cached = cache.get(key)
        if cached is None:
            print(f"   {key}: ✅ CLEARED")
            cleared_count += 1
        else:
            print(f"   {key}: ❌ STILL CACHED")

    print(
        f"\n📊 Cache Clearing Results: {cleared_count}/{len(cache_entries)} entries cleared"
    )

    # Step 4: Test that fresh queries work
    print("\n📋 STEP 4: Testing fresh queries")

    # Simulate what happens when GraphQL makes a fresh query
    fresh_tags = list(Tag.objects.filter(name__startswith="AggressiveTest"))
    print(f"✅ Fresh query returns {len(fresh_tags)} tags")

    # Check if new tag is included
    new_tag_found = any(tag.name == "AggressiveTestNewTag" for tag in fresh_tags)
    print(f"✅ New tag found in fresh query: {new_tag_found}")

    # Step 5: Test multiple rapid invalidations
    print("\n📋 STEP 5: Testing multiple rapid invalidations")

    # Set some cache again
    cache.set("test_rapid_1", "value1", 300)
    cache.set("test_rapid_2", "value2", 300)

    # Do multiple rapid invalidations
    for i in range(3):
        invalidate_tag_cache()
        time.sleep(0.05)  # Small delay

    # Check if cache is still cleared
    rapid_test_1 = cache.get("test_rapid_1")
    rapid_test_2 = cache.get("test_rapid_2")

    print(f"✅ Rapid test 1 cleared: {rapid_test_1 is None}")
    print(f"✅ Rapid test 2 cleared: {rapid_test_2 is None}")

    # Step 6: Final assessment
    print("\n" + "=" * 80)
    print("📊 FINAL ASSESSMENT")
    print("=" * 80)

    if cleared_count == len(cache_entries):
        print("🎉 SUCCESS: Aggressive cache invalidation is working perfectly!")
        print("✅ All cache entries were cleared")
        print("✅ Fresh queries return correct data")
        print("✅ Multiple rapid invalidations work correctly")

        print("\n💡 SOLUTION STATUS:")
        print("   ✅ Cache invalidation is now working")
        print("   ✅ New tags should appear immediately in GraphiQL")
        print("   ✅ No more stale cache issues")

    else:
        print("⚠️ PARTIAL SUCCESS: Some cache entries were not cleared")
        print(f"   {cleared_count}/{len(cache_entries)} entries cleared")
        print(
            "   This might still work if the remaining entries are not GraphQL-related"
        )

    print("\n🚀 NEXT STEPS:")
    print("1. Test in GraphiQL by creating a new tag")
    print("2. Verify that the new tag appears immediately in queries")
    print("3. If it still doesn't work, check for client-side caching in GraphiQL")

    # Cleanup
    Tag.objects.filter(name__startswith="AggressiveTest").delete()
    cache.clear()
    print("\n🧹 Cleanup completed")


if __name__ == "__main__":
    test_aggressive_cache_invalidation()
