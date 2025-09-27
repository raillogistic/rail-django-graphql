#!/usr/bin/env python3
"""
Test script to verify the timeout parameter fix for CacheManager.set_query_result
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')

# Setup Django
django.setup()

from django_graphql_auto.extensions.optimization import get_cache_manager

def test_timeout_parameter():
    """Test that set_query_result accepts timeout parameter"""
    print("🧪 Testing CacheManager timeout parameter fix...")
    
    # Get cache manager instance
    cache_manager = get_cache_manager()
    
    # Test data
    query_string = "{ tags { name } }"
    test_result = {"data": {"tags": [{"name": "test"}]}}
    variables = {"limit": 10}
    user_id = 123
    custom_timeout = 600  # 10 minutes
    
    try:
        # Test 1: Call set_query_result with timeout parameter
        print("✅ Test 1: Calling set_query_result with timeout parameter...")
        cache_manager.set_query_result(
            query_string=query_string,
            result=test_result,
            variables=variables,
            user_id=user_id,
            timeout=custom_timeout
        )
        print(f"   ✓ Successfully called with timeout={custom_timeout}")
        
        # Test 2: Call set_query_result without timeout parameter
        print("✅ Test 2: Calling set_query_result without timeout parameter...")
        cache_manager.set_query_result(
            query_string=query_string,
            result=test_result,
            variables=variables,
            user_id=user_id
        )
        print("   ✓ Successfully called without timeout (using default)")
        
        # Test 3: Verify the method signature accepts timeout
        print("✅ Test 3: Verifying method signature...")
        import inspect
        sig = inspect.signature(cache_manager.set_query_result)
        params = list(sig.parameters.keys())
        print(f"   Method parameters: {params}")
        
        if 'timeout' in params:
            print("   ✓ timeout parameter is present in method signature")
        else:
            print("   ❌ timeout parameter is missing from method signature")
            return False
            
        # Test 4: Test with keyword argument (as used in the error)
        print("✅ Test 4: Testing with keyword argument syntax...")
        cache_manager.set_query_result(
            query_string, test_result, variables, user_id, timeout=custom_timeout
        )
        print("   ✓ Successfully called with keyword timeout argument")
        
        print("\n🎉 All timeout parameter tests passed!")
        print("The GraphQL query 'tags' should now work without the timeout error.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_timeout_parameter()
    sys.exit(0 if success else 1)