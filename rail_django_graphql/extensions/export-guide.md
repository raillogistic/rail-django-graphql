# Django Model Export Guide

This guide covers the enhanced Django model export functionality that allows you to generate Excel and CSV files from Django models with flexible field configurations and advanced GraphQL filter integration.

## Table of Contents

1. [Overview](#overview)
2. [Field Format Options](#field-format-options)
3. [GraphQL Filter Integration](#graphql-filter-integration)
4. [HTTP API Usage](#http-api-usage)
5. [Python API Usage](#python-api-usage)
6. [Advanced Examples](#advanced-examples)
7. [Integration Setup](#integration-setup)
8. [Error Handling](#error-handling)
9. [Performance Considerations](#performance-considerations)

## Overview

The Django model export functionality provides:

- **Flexible Field Configuration**: Support for both string and dictionary field formats
- **GraphQL Filter Integration**: Uses the same advanced filtering as GraphQL queries
- **Multiple Export Formats**: Excel (.xlsx) and CSV support
- **HTTP API Endpoint**: RESTful API for generating exports
- **Python API**: Direct programmatic access to export functionality
- **Advanced Field Access**: Support for nested fields, methods, and properties

## Field Format Options

### String Format

The simplest way to specify fields is using strings. The field name serves as both the accessor and the title (using the model field's `verbose_name`).

```python
fields = [
    "title",           # Uses field's verbose_name as title
    "author.username", # Nested field access
    "created_at",      # Date field
    "is_published"     # Boolean field
]
```

### Dictionary Format

For more control over field titles and complex accessors, use dictionary format:

```python
fields = [
    {"accessor": "title", "title": "Post Title"},
    {"accessor": "author.username", "title": "Author Name"},
    {"accessor": "slug"},  # Uses verbose_name as title
    {"accessor": "tags.count", "title": "Number of Tags"}
]
```

### Mixed Format

You can combine both formats in the same export:

```python
fields = [
    "title",  # String format
    {"accessor": "author.username", "title": "Author"},  # Dict format
    "created_at",  # String format
    {"accessor": "view_count", "title": "Views"}  # Dict format
]
```

## GraphQL Filter Integration

The export functionality integrates with the same GraphQL filter classes used in queries, providing advanced filtering capabilities beyond basic Django ORM filters.

### Basic Filters

```python
filters = {
    "status": "published",
    "is_featured": True,
    "author__is_active": True
}
```

### Quick Search Filters

```python
filters = {
    "quick": "django tutorial",  # Searches across configured quick_filter_fields
    "status": "published"
}
```

### Date Filters

```python
filters = {
    "created_date_today": True,
    "updated_date_this_week": True,
    "published_date_last_month": True,
    "archived_date_between": ["2024-01-01", "2024-12-31"]
}
```

### Custom Filters

```python
filters = {
    "has_tags": True,           # Custom filter defined in GraphQLMeta
    "content_length": "medium", # Custom filter with choices
    "reading_time_range": "5-10" # Custom filter with range
}
```

### Complex Filters

```python
filters = {
    "category__name__in": ["Technology", "Programming"],
    "view_count__gte": 100,
    "tags__name__icontains": "python",
    "author__profile__verified": True,
    "comments__count__range": [5, 50]
}
```

## HTTP API Usage

### Endpoint

```
POST /api/export/
```

### Request Format

```json
{
    "app_name": "blog",
    "model_name": "Post",
    "file_extension": "xlsx",  // or "csv"
    "filename": "blog_posts_export",
    "fields": [
        "title",
        "author.username",
        {"accessor": "slug", "title": "URL Slug"},
        {"accessor": "created_at", "title": "Publication Date"}
    ],
    "ordering": ["-created_at", "title"],
    "variables": {
        "status": "published",
        "quick": "django tutorial",
        "created_date_this_month": True,
        "author__is_active": True
    }
}
```

### Response

The API returns the file as a downloadable attachment with appropriate headers:

- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Excel) or `text/csv` (CSV)
- **Content-Disposition**: `attachment; filename="blog_posts_export.xlsx"`

### Error Responses

```json
{
    "error": "Validation error",
    "details": "Invalid field configuration at index 2: field must be string or dict with accessor/title"
}
```

### API Documentation Endpoint

```
GET /api/export/
```

Returns API documentation and examples.

## Python API Usage

### Direct Functions

```python
from rail_django_graphql.extensions.exporting import export_model_to_csv, export_model_to_excel

# Export to CSV
csv_content = export_model_to_csv(
    app_name="blog",
    model_name="Post",
    fields=["title", {"accessor": "author.username", "title": "Author"}],
    filters={"status": "published", "quick": "django"},
    ordering=["-created_at"]
)

# Save to file
with open("posts.csv", "wb") as f:
    f.write(csv_content)

# Export to Excel
excel_content = export_model_to_excel(
    app_name="blog",
    model_name="Post",
    fields=["title", "author.username", "created_at"],
    filters={"is_featured": True},
    ordering=["-view_count"]
)

with open("featured_posts.xlsx", "wb") as f:
    f.write(excel_content)
```

### ModelExporter Class

```python
from rail_django_graphql.extensions.exporting import ModelExporter

# Initialize exporter
exporter = ModelExporter("blog", "Post")

# Define fields and filters
fields = [
    "title",
    {"accessor": "author.username", "title": "Author"},
    {"accessor": "category.name", "title": "Category"},
    "created_at"
]

filters = {
    "status": "published",
    "created_date_this_week": True,
    "author__is_staff": False
}

ordering = ["-created_at", "title"]

# Export to both formats
csv_data = exporter.export_to_csv(fields, filters, ordering)
excel_data = exporter.export_to_excel(fields, filters, ordering)

# Save files
with open("posts.csv", "wb") as f:
    f.write(csv_data)

with open("posts.xlsx", "wb") as f:
    f.write(excel_data)
```

## Advanced Examples

### Complex Nested Field Access

```python
fields = [
    "title",
    {"accessor": "author.profile.full_name", "title": "Author Full Name"},
    {"accessor": "author.profile.bio", "title": "Author Bio"},
    {"accessor": "category.parent.name", "title": "Parent Category"},
    {"accessor": "tags.count", "title": "Tag Count"},
    {"accessor": "comments.filter(is_approved=True).count", "title": "Approved Comments"},
    {"accessor": "get_absolute_url", "title": "URL"},
    {"accessor": "word_count", "title": "Word Count"},  # Custom property
    {"accessor": "reading_time", "title": "Reading Time"}  # Custom method
]
```

### Advanced Filtering

```python
filters = {
    # Basic filters
    "status": "published",
    "is_featured": True,
    
    # Quick search
    "quick": "python django tutorial",
    
    # Date filters
    "created_date_this_month": True,
    "updated_date_last_week": True,
    
    # Range filters
    "view_count__range": [100, 10000],
    "word_count__gte": 500,
    
    # Nested relationship filters
    "author__profile__verified": True,
    "category__parent__slug": "technology",
    "tags__name__in": ["python", "django", "web-development"],
    
    # Custom filters (defined in GraphQLMeta)
    "has_tags": True,
    "content_length": "medium",
    "reading_difficulty": "intermediate"
}
```

### E-commerce Product Export

```python
# Product export with complex relationships
fields = [
    "name",
    {"accessor": "sku", "title": "Product SKU"},
    {"accessor": "price", "title": "Price ($)"},
    {"accessor": "category.name", "title": "Category"},
    {"accessor": "category.parent.name", "title": "Parent Category"},
    {"accessor": "supplier.company_name", "title": "Supplier"},
    {"accessor": "supplier.contact_email", "title": "Supplier Email"},
    {"accessor": "stock_quantity", "title": "Stock"},
    {"accessor": "variants.count", "title": "Variants"},
    {"accessor": "reviews.count", "title": "Reviews"},
    {"accessor": "average_rating", "title": "Rating"},
    {"accessor": "is_active", "title": "Active"}
]

filters = {
    "is_active": True,
    "stock_quantity__gt": 0,
    "price__range": [10, 1000],
    "category__is_featured": True,
    "supplier__is_verified": True,
    "reviews__count__gte": 5,
    "average_rating__gte": 4.0,
    "quick": "electronics smartphone",
    "created_date_last_month": True
}

ordering = ["category.name", "-average_rating", "-reviews__count"]
```

## Integration Setup

### 1. Add to URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('api/', include('rail_django_graphql.extensions.urls')),
]
```

### 2. Import in Your Code

```python
# views.py or services.py
from rail_django_graphql.extensions.exporting import (
    ModelExporter,
    export_model_to_csv,
    export_model_to_excel
)
```

### 3. Configure GraphQL Meta (Optional)

To use advanced filters, ensure your models have proper GraphQL configuration:

```python
# models.py
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = ['title', 'author', 'created_at']
        quick_filter_fields = ['title', 'content']
        custom_filters = {
            'has_tags': 'tags__isnull',
            'content_length': {
                'short': 'content__length__lt',
                'medium': 'content__length__range',
                'long': 'content__length__gt'
            }
        }
```

## Error Handling

### Common Errors

1. **Invalid Field Configuration**
   ```json
   {
       "error": "Invalid field configuration at index 2",
       "details": "Field must be string or dict with accessor/title"
   }
   ```

2. **Model Not Found**
   ```json
   {
       "error": "Model not found",
       "details": "Model 'InvalidModel' not found in app 'blog'"
   }
   ```

3. **Field Access Error**
   - Fields that don't exist or can't be accessed are logged as warnings
   - Empty string is used as fallback value

### Error Logging

The system logs errors for debugging:

```python
import logging

# Configure logging to see export errors
logging.getLogger('rail_django_graphql.extensions.exporting').setLevel(logging.WARNING)
```

## Performance Considerations

### Optimization Tips

1. **Limit Result Sets**: Use appropriate filters to limit the number of records
2. **Select Related**: The system automatically optimizes queries for foreign key fields
3. **Prefetch Related**: Many-to-many and reverse foreign key relationships are optimized
4. **Field Selection**: Only include necessary fields to reduce processing time
5. **Ordering**: Use database-level ordering instead of Python sorting

### Large Dataset Handling

For very large datasets, consider:

```python
# Use pagination or chunking for large exports
filters = {
    "created_at__gte": "2024-01-01",
    "created_at__lt": "2024-02-01"  # Monthly chunks
}

# Limit fields to essential data only
fields = ["id", "title", "created_at"]  # Minimal field set
```

### Memory Usage

- CSV exports are more memory-efficient than Excel
- Excel exports load all data into memory for formatting
- Consider CSV for very large datasets (>100k records)

## Security Considerations

1. **Authentication**: Implement proper authentication for the export endpoint
2. **Authorization**: Ensure users can only export data they have permission to view
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Data Sanitization**: Be cautious with user-provided field accessors

### Example Security Implementation

```python
# views.py - Custom secure export view
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rail_django_graphql.extensions.exporting import ExportView

@method_decorator(login_required, name='dispatch')
class SecureExportView(ExportView):
    def post(self, request):
        # Add custom authorization logic
        if not request.user.has_perm('myapp.export_data'):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        return super().post(request)
```

## Troubleshooting

### Common Issues

1. **GraphQL Filters Not Working**
   - Ensure `AdvancedFilterGenerator` is properly configured
   - Check that your model has `GraphQLMeta` configuration
   - Verify filter field names match your model fields

2. **Nested Field Access Fails**
   - Check that all relationships exist and are properly defined
   - Ensure foreign key fields are not null
   - Use `select_related` optimization for better performance

3. **Export Takes Too Long**
   - Add appropriate filters to limit result set
   - Reduce the number of fields being exported
   - Consider using CSV instead of Excel for large datasets

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'rail_django_graphql.extensions.exporting': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

This comprehensive guide covers all aspects of the enhanced Django model export functionality. The system provides flexible field configuration, advanced GraphQL filter integration, and robust error handling for reliable data export operations.