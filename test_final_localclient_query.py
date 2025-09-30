#!/usr/bin/env python
"""
Final test for LocalClient info query
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.core.schema import get_schema_builder

def test_final_localclient_query():
    print("=== Final LocalClient Info Query Test ===")
    
    # Get the schema
    schema_builder = get_schema_builder()
    schema = schema_builder.get_schema()
    
    # The original query that was failing
    query = """
    {
        localclients {
            info {
                id
            }
        }
    }
    """
    
    print("Executing the original query:")
    print(query)
    
    result = schema.execute(query)
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
        return False
    
    if result.data:
        print("\n✓ Success! Query executed without errors")
        print("Data:")
        localclients = result.data.get('localclients', [])
        print(f"Found {len(localclients)} LocalClients")
        
        for i, client in enumerate(localclients):
            info = client.get('info')
            if info:
                print(f"  LocalClient {i+1}: info.id = {info['id']}")
            else:
                print(f"  LocalClient {i+1}: info = null")
        
        return True
    
    print("No data returned")
    return False

if __name__ == "__main__":
    success = test_final_localclient_query()
    if success:
        print("\n🎉 The LocalClient info query is now working correctly!")
    else:
        print("\n❌ The query is still failing")