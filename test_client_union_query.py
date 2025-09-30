#!/usr/bin/env python
"""
Test Client union query to verify polymorphic type resolution
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
from test_app.models import LocalClient, ClientInformation, Client

def test_client_union_query():
    """Test querying a client that is actually a LocalClient instance using union types."""
    
    output_file = "test_client_union_output.txt"
    
    with open(output_file, "w") as f:
        # Create a LocalClient instance
        local_client = LocalClient.objects.create(
            raison="Test Local Client Union",
            test="Test Value Union"
        )
        
        # Create associated ClientInformation
        client_info = ClientInformation.objects.create(
            client=local_client,
            adresse="123 Union Test Street",
            ville="Union Test City",
            code_postal="12345",
            pays="Union Test Country",
            paysx="Union Test Country X"
        )
        
        f.write(f"Created LocalClient with ID: {local_client.id}\n")
        f.write(f"LocalClient type: {type(local_client)}\n")
        f.write(f"LocalClient is instance of Client: {isinstance(local_client, Client)}\n")
        
        # Get the schema
        schema_builder = get_schema_builder()
        schema = schema_builder.get_schema()
        
        # Test GraphQL query using client query with union type
        query = f'''
        {{
            client(id:"{local_client.id}") {{
                ... on LocalClientType {{
                    id
                    raison
                    test
                    info {{
                        adresse
                    }}
                }}
                ... on ClientType {{
                    id
                    raison
                    info {{
                        adresse
                    }}
                }}
            }}
        }}
        '''
        
        f.write(f"\nExecuting GraphQL query with union fragments:\n")
        f.write(query)
        f.write("\n")
        
        try:
            result = schema.execute(query)
            
            f.write(f"\nGraphQL execution completed\n")
            f.write(f"Has errors: {bool(result.errors)}\n")
            
            if result.errors:
                f.write("\nGraphQL Errors:\n")
                for error in result.errors:
                    f.write(f"  - {error}\n")
            else:
                f.write("\nGraphQL Result:\n")
                import json
                f.write(json.dumps(result.data, indent=2))
                f.write("\n")
        
        except Exception as e:
            f.write(f"\nException occurred: {e}\n")
        
        finally:
            # Clean up
            try:
                client_info.delete()
                local_client.delete()
                f.write(f"\nCleaned up LocalClient {local_client.id}\n")
            except Exception as e:
                f.write(f"\nError during cleanup: {e}\n")

if __name__ == "__main__":
    test_client_union_query()
    print("Test completed. Check test_client_union_output.txt for results.")