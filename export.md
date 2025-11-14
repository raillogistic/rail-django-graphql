# Data Export API Guide

This document explains how frontend developers can export Django model data to CSV or Excel using the HTTP export endpoint implemented in rail_django_graphql/extensions/exporting.py.

Overview
- Provides a simple HTTP endpoint to download data as CSV (.csv) or Excel (.xlsx)
- Supports dynamic model selection by app_name and model_name
- Allows flexible field selection, including nested relations and method calls
- Integrates with GraphQL-style filters; falls back to basic Django ORM filters
- Supports simple ordering
- Includes structured error handling

Authentication
- The endpoint is designed to be JWT-protected when jwt_required middleware is available
- Send the Authorization header: `Authorization: Bearer <jwt_token>`
- If jwt_required is not configured, authentication may be bypassed (development only)

Endpoint
- Method: POST
- Path: /api/export/
- Content-Type: application/json

Request Body
- app_name: string
  - Django app label where the model resides (e.g., "blog")
- model_name: string
  - Django model class name (e.g., "BlogPost")
- file_extension: string
  - "csv" or "xlsx" (Excel requires openpyxl to be installed on the server)
- filename: string (optional)
  - Base name of the file to download (without extension). If omitted, a default name is used
- fields: array of strings or objects
  - Defines which fields to include in the export and their column titles
  - Accepted formats:
    - String: "field_name" (uses field_name as accessor and the field’s verbose_name as the title)
    - Object: { "accessor": "author.username", "title": "Author Username" }
  - Supported accessor behaviors:
    - Simple fields: "title"
    - Nested fields via relations: "author.username"
    - Method calls: "get_absolute_url()" (method will be called on the instance)
    - Many-to-many fields: returns a comma-separated string of related object names
- ordering: string (optional)
  - Django ORM ordering expression, e.g., "created_at" or "-created_at"
- variables: object (optional)
  - Filter parameters for the export. Two modes are supported:
    1) GraphQL filter integration (AdvancedFilterGenerator): If available, variables are passed directly into the generated filter set. Use the filter fields defined for your model’s GraphQL filters (e.g., quick search, date filters, custom filters).
    2) Fallback to Django ORM filtering: If GraphQL filters are unavailable or invalid, variables are applied as QuerySet.filter(**variables). You can use Django lookup expressions like "title__icontains": "hello" or "status": "active".

Field Values and Formatting
- None values are exported as an empty string
- Booleans: "Yes" or "No"
- Datetime: "YYYY-MM-DD HH:MM:SS" (timezone-aware datetimes are converted to local time)
- Date: "YYYY-MM-DD"
- Decimal: converted to float
- Related objects: string representation (str(obj))
- Many-to-many: comma-separated list of related object string representations

Responses
- Success (CSV):
  - Content-Type: text/csv
  - Content-Disposition: attachment; filename="<filename>.csv"
  - Body: CSV content
- Success (Excel):
  - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - Content-Disposition: attachment; filename="<filename>.xlsx"
  - Body: binary Excel file (.xlsx)
- Error (JSON):
  - Content-Type: application/json
  - Body: { "error": "message" } or a structured error message; HTTP status will indicate failure

Examples

1) curl (CSV)
```
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{
    "app_name": "blog",
    "model_name": "BlogPost",
    "file_extension": "csv",
    "filename": "blog_posts_export",
    "fields": [
      "id",
      {"accessor": "title", "title": "Title"},
      {"accessor": "author.username", "title": "Author"},
      {"accessor": "get_absolute_url()", "title": "URL"},
      {"accessor": "tags", "title": "Tags"}
    ],
    "ordering": "-created_at",
    "variables": {"status": "PUBLISHED", "title__icontains": "hello"}
  }' \
  -o blog_posts_export.csv \
  http://localhost:8000/api/export/
```

2) curl (Excel)
```
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{
    "app_name": "shop",
    "model_name": "Order",
    "file_extension": "xlsx",
    "filename": "orders_export",
    "fields": [
      "id",
      {"accessor": "customer.email", "title": "Customer Email"},
      {"accessor": "total", "title": "Total"},
      {"accessor": "created_at", "title": "Created"}
    ],
    "ordering": "-created_at",
    "variables": {"status": "PAID"}
  }' \
  --output orders_export.xlsx \
  http://localhost:8000/api/export/
```

3) Browser fetch (CSV)
```
async function downloadCsv() {
  const body = {
    app_name: 'blog',
    model_name: 'BlogPost',
    file_extension: 'csv',
    filename: 'blog_posts_export',
    fields: [
      'id',
      { accessor: 'title', title: 'Title' },
      { accessor: 'author.username', title: 'Author' },
    ],
    ordering: '-created_at',
    variables: { status: 'PUBLISHED' },
  };

  const res = await fetch('/api/export/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + getJwt(),
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Export failed');
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = body.filename + '.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
```

4) Axios (Excel)
```
import axios from 'axios';

async function downloadExcel() {
  const body = {
    app_name: 'shop',
    model_name: 'Order',
    file_extension: 'xlsx',
    filename: 'orders_export',
    fields: [
      'id',
      { accessor: 'customer.email', title: 'Customer Email' },
      { accessor: 'total', title: 'Total' },
      { accessor: 'created_at', title: 'Created' }
    ],
    ordering: '-created_at',
    variables: { status: 'PAID' },
  };

  const res = await axios.post('/api/export/', body, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + getJwt(),
    },
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', body.filename + '.xlsx');
  document.body.appendChild(link);
  link.click();
  link.remove();
}
```

Filtering Notes
- When AdvancedFilterGenerator is available, prefer its defined filter fields (e.g., quick search, date ranges, custom filters). Check your GraphQL filter docs for the specific variable names (see docs/graphql-meta-guide.md and generators/filters.py).
- Fallback filtering uses Django field lookups. Examples:
  - { "title__icontains": "hello" }
  - { "status": "PUBLISHED" }
  - { "created_at__date": "2024-11-10" }
  - { "total__gte": 100 }
- Empty or null values in variables are stripped before filtering.

Ordering
- Provide a single ordering string, e.g., "created_at" or "-created_at"
- Multiple-field ordering is not supported by the current endpoint implementation (submit one field only)

Excel Availability
- The server attempts to import openpyxl; if unavailable, Excel exports will not work
- Ensure openpyxl is installed on the server environment if you need .xlsx output

Error Handling
- On server errors (invalid model, bad field access, filtering failures), the endpoint returns a JSON error response and an appropriate HTTP status
- Frontend should check `res.ok` and handle non-200 statuses gracefully

Security Notes
- Use HTTPS and send Authorization: Bearer <jwt_token>
- The view is CSRF-exempt to support API usage from SPAs/native clients
- Validate/sanitize user-provided variables on the client side when building requests
- Avoid extremely broad exports; apply filters and ordering to keep payload sizes manageable

Best Practices
- Always specify a filename to make user downloads clear
- Limit fields to only those needed by the user
- Use nested accessors for relation fields (e.g., author.username) rather than dumping entire related objects
- For large datasets, consider server-side pagination or segmented exports (if available)
- If you need specific column titles, use the object format for fields:
  - { "accessor": "author.username", "title": "Author" }

Troubleshooting
- "Model not found": Verify app_name/model_name values and that the model is installed
- "Excel export not available": Install openpyxl on the server
- "Empty export": Check filters and ensure records match your variables
- "Method call failed": If using method accessors like get_absolute_url(), confirm the method exists and is callable

Change Log and Compatibility
- This guide corresponds to the implementation in rail_django_graphql/extensions/exporting.py
- If the endpoint’s contract changes, update this guide accordingly