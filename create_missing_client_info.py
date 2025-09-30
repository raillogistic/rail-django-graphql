#!/usr/bin/env python
"""
Create missing ClientInformation records for LocalClients
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import LocalClient, ClientInformation


def create_missing_client_info():
    print("=== Creating Missing ClientInformation Records ===")

    # Find LocalClients without info
    local_clients_without_info = []

    for local_client in LocalClient.objects.all():
        try:
            # Try to access the info field
            info = local_client.info
        except ClientInformation.DoesNotExist:
            local_clients_without_info.append(local_client)

    print(f"Found {len(local_clients_without_info)} LocalClients without info")

    # Create ClientInformation for each LocalClient without info
    created_count = 0
    for local_client in local_clients_without_info:
        client_info = ClientInformation.objects.create(
            client=local_client,
            adresse=f"Default Address for {local_client.raison}",
            ville="Default City",
            code_postal="00000",
            pays="Default Country",
            paysx="Default Country X",
        )
        print(
            f"Created ClientInformation {client_info.id} for LocalClient {local_client.id}"
        )
        created_count += 1

    print(f"\nCreated {created_count} ClientInformation records")

    # Verify all LocalClients now have info
    print("\n=== Verification ===")
    all_local_clients = LocalClient.objects.all()
    clients_with_info = 0

    for local_client in all_local_clients:
        try:
            info = local_client.info
            clients_with_info += 1
        except ClientInformation.DoesNotExist:
            print(f"LocalClient {local_client.id} still has no info!")

    print(f"Total LocalClients: {all_local_clients.count()}")
    print(f"LocalClients with info: {clients_with_info}")

    if clients_with_info == all_local_clients.count():
        print("✓ All LocalClients now have ClientInformation records")
    else:
        print("✗ Some LocalClients still missing ClientInformation")


if __name__ == "__main__":
    create_missing_client_info()
