import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Available tables:")
for table in tables:
    print(f"  - {table}")

# Check if Client table exists
client_tables = [t for t in tables if 'client' in t.lower()]
print(f"\nClient-related tables: {client_tables}")