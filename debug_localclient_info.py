#!/usr/bin/env python
"""
Debug script to check LocalClient and ClientInformation relationship
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import LocalClient, ClientInformation, Client


def debug_localclient_info():
    print("=== LocalClient and ClientInformation Debug ===")

    # Check if we have any LocalClient instances
    local_clients = LocalClient.objects.all()
    print(f"Total LocalClient instances: {local_clients.count()}")

    # Check if we have any ClientInformation instances
    client_infos = ClientInformation.objects.all()
    print(f"Total ClientInformation instances: {client_infos.count()}")

    # Check if we have any Client instances
    clients = Client.objects.all()
    print(f"Total Client instances: {clients.count()}")

    print("\n=== LocalClient Details ===")
    for i, local_client in enumerate(local_clients[:5]):  # Show first 5
        print(f"LocalClient {i+1}:")
        print(f"  ID: {local_client.id}")
        print(f"  Raison: {local_client.raison}")
        print(f"  Test: {local_client.test}")

        # Check if it has info
        try:
            info = local_client.info
            print(f"  Info: {info}")
            print(f"  Info ID: {info.id}")
            print(f"  Info Adresse: {info.adresse}")
        except ClientInformation.DoesNotExist:
            print(f"  Info: None (DoesNotExist)")
        except AttributeError as e:
            print(f"  Info: AttributeError - {e}")

        print()

    print("\n=== ClientInformation Details ===")
    for i, info in enumerate(client_infos[:5]):  # Show first 5
        print(f"ClientInformation {i+1}:")
        print(f"  ID: {info.id}")
        print(f"  Client ID: {info.client.id}")
        print(f"  Client Type: {type(info.client).__name__}")
        print(f"  Adresse: {info.adresse}")
        print()

    # Test creating a LocalClient with info
    print("\n=== Creating Test Data ===")
    try:
        # Create a LocalClient
        local_client = LocalClient.objects.create(
            raison="Test Client", test="Test Value"
        )
        print(f"Created LocalClient: {local_client.id}")

        # Create ClientInformation for this LocalClient
        client_info = ClientInformation.objects.create(
            client=local_client,
            adresse="123 Test Street",
            ville="Test City",
            code_postal="12345",
            pays="Test Country",
            paysx="Test Country X",
        )
        print(f"Created ClientInformation: {client_info.id}")

        # Test accessing info from LocalClient
        print(f"LocalClient.info: {local_client.info}")
        print(f"LocalClient.info.adresse: {local_client.info.adresse}")

    except Exception as e:
        print(f"Error creating test data: {e}")

    print("\n=== Model Field Analysis ===")
    print("LocalClient fields:")
    for field in LocalClient._meta.get_fields():
        print(f"  {field.name}: {type(field).__name__}")

    print("\nClient fields:")
    for field in Client._meta.get_fields():
        print(f"  {field.name}: {type(field).__name__}")


if __name__ == "__main__":
    debug_localclient_info()
