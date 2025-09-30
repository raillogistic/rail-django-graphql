import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Client, LocalClient, ClientInformation
from django_graphql_auto.core.schema import SchemaBuilder
import graphene


def test_client_type_query():
    """Test that clients query returns ClientType instead of a union."""
    print("Testing client type query...")
    
    # Clean up any existing data first
    try:
        ClientInformation.objects.all().delete()
        LocalClient.objects.all().delete()
        Client.objects.all().delete()
    except Exception as e:
        print(f"Cleanup error (expected if tables don't exist): {e}")
    
    try:
        # Create test data
        client = Client.objects.create(raison="Test Client")
        local_client = LocalClient.objects.create(raison="Test Local Client", test="Test Value")
        
        # Create ClientInformation objects
        client_info = ClientInformation.objects.create(
            client=client,
            code_postal="12345",
            pays="France",
            paysx="FranceX"
        )
        
        local_client_info = ClientInformation.objects.create(
            client=local_client,
            code_postal="67890",
            pays="Germany",
            paysx="GermanyX"
        )
        
        # Build schema
        builder = SchemaBuilder()
        schema = builder.get_schema()
        
        # Test query
        query = """
        query {
            clients {
                id
                raison
                uppercaseRaison
                info {
                    id
                    codePostal
                    pays
                }
            }
        }
        """
        
        result = schema.execute(query)
        
        if result.errors:
            print(f"GraphQL errors: {result.errors}")
            return False
        
        # Validate results
        clients_data = result.data['clients']
        print(f"Retrieved {len(clients_data)} clients")
        
        # Check that we got both clients
        assert len(clients_data) == 2, f"Expected 2 clients, got {len(clients_data)}"
        
        # Check that both clients have the expected fields
        for client_data in clients_data:
            assert 'id' in client_data
            assert 'raison' in client_data
            assert 'uppercaseRaison' in client_data
            assert 'info' in client_data
            
            # Validate info sub-object
            info_data = client_data['info']
            assert 'id' in info_data
            assert 'codePostal' in info_data
            assert 'pays' in info_data
        
        print("✅ SUCCESS: Clients query returns ClientType for both Client and LocalClient instances")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test data
        try:
            ClientInformation.objects.all().delete()
            LocalClient.objects.all().delete()
            Client.objects.all().delete()
        except Exception as e:
            print(f"Final cleanup error: {e}")


if __name__ == "__main__":
    success = test_client_type_query()
    sys.exit(0 if success else 1)