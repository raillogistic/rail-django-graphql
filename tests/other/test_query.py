import graphene
from rail_django_graphql.schema import schema

query = """
query {
  comment_pages(page: 1, per_page: 5, is_approved: true, order_by: ["-created_at"]) {
    items {
      id
      content
    }
    page_info {
      total_count
      page_count
      current_page
      per_page
      has_next_page
      has_previous_page
    }
  }
}
"""

result = schema.execute(query)
if result.errors:
    print("Errors:", result.errors)
else:
    print("Success:", result.data)
