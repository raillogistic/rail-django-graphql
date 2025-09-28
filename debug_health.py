import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.schema import schema
from django_graphql_auto.extensions.health import HealthQuery

# Check if HealthQuery has the resolver methods
print('HealthQuery methods:')
for attr in dir(HealthQuery):
    if 'resolve' in attr:
        print(f'  {attr}: {getattr(HealthQuery, attr)}')

# Check the schema field resolvers using GraphQL introspection
query_type = schema.graphql_schema.get_type('Query')
health_status_field = query_type.fields.get('health_status')
system_metrics_field = query_type.fields.get('system_metrics')

print(f'health_status field resolver: {health_status_field.resolve if health_status_field else "Not found"}')
print(f'system_metrics field resolver: {system_metrics_field.resolve if system_metrics_field else "Not found"}')

# Try to execute the resolver directly
if health_status_field and health_status_field.resolve:
    try:
        result = health_status_field.resolve(None, None)
        print(f'Direct resolver result: {result}')
    except Exception as e:
        print(f'Direct resolver error: {e}')

# Test the GraphQL query execution
from graphql import graphql_sync
result = graphql_sync(schema.graphql_schema, '{ health_status { overall_status } }')
print(f'GraphQL query result: {result.data}')
if result.errors:
    print(f'GraphQL query errors: {result.errors}')