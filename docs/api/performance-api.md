# Performance Monitoring API

The performance monitoring system provides REST API endpoints to access performance metrics, alerts, and query statistics.

## Base URL

All performance API endpoints are available under:
```
/graphql/performance/
```

## Authentication

Performance endpoints respect Django's authentication system. Ensure users have appropriate permissions to access performance data.

## Endpoints

### GET /graphql/performance/

Main performance endpoint that supports different actions via query parameters.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | No | `stats` | Action to perform: `stats`, `alerts`, `slow_queries` |
| `limit` | integer | No | 50 | Maximum number of results to return |
| `offset` | integer | No | 0 | Number of results to skip |
| `start_date` | string | No | - | Start date filter (ISO format) |
| `end_date` | string | No | - | End date filter (ISO format) |

#### Actions

##### 1. Performance Statistics (`action=stats`)

Returns overall performance statistics and metrics.

**Request:**
```bash
GET /graphql/performance/?action=stats
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "overview": {
      "total_requests": 15420,
      "avg_response_time_ms": 245.7,
      "slow_queries_count": 23,
      "error_rate": 0.02,
      "uptime_hours": 168.5
    },
    "performance_metrics": {
      "avg_query_time_ms": 156.3,
      "avg_db_time_ms": 89.2,
      "avg_cache_time_ms": 12.1,
      "avg_memory_usage_mb": 45.8,
      "cache_hit_rate": 0.87
    },
    "query_complexity": {
      "avg_complexity": 15.2,
      "max_complexity": 89,
      "high_complexity_queries": 12
    },
    "database_stats": {
      "avg_queries_per_request": 3.4,
      "slow_db_queries": 8,
      "connection_pool_usage": 0.65
    },
    "recent_trends": {
      "response_time_trend": "stable",
      "error_rate_trend": "decreasing",
      "memory_usage_trend": "increasing"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### 2. Performance Alerts (`action=alerts`)

Returns recent performance alerts and warnings.

**Request:**
```bash
GET /graphql/performance/?action=alerts&limit=20
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "id": "alert_001",
        "type": "slow_query",
        "severity": "warning",
        "message": "Query exceeded slow threshold",
        "details": {
          "query_time_ms": 1250,
          "threshold_ms": 1000,
          "operation_name": "GetUserProfile",
          "query_hash": "abc123def456"
        },
        "timestamp": "2024-01-15T10:25:30Z",
        "resolved": false
      },
      {
        "id": "alert_002",
        "type": "high_complexity",
        "severity": "error",
        "message": "Query complexity exceeded maximum limit",
        "details": {
          "complexity_score": 125,
          "max_complexity": 100,
          "operation_name": "GetComplexData",
          "query_hash": "def456ghi789"
        },
        "timestamp": "2024-01-15T10:20:15Z",
        "resolved": true
      },
      {
        "id": "alert_003",
        "type": "memory_warning",
        "severity": "warning",
        "message": "Memory usage exceeded threshold",
        "details": {
          "memory_usage_mb": 120,
          "threshold_mb": 100,
          "peak_memory_mb": 135
        },
        "timestamp": "2024-01-15T10:15:45Z",
        "resolved": false
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_next": true
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### 3. Slow Queries (`action=slow_queries`)

Returns information about the slowest GraphQL queries.

**Request:**
```bash
GET /graphql/performance/?action=slow_queries&limit=10
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "slow_queries": [
      {
        "id": "query_001",
        "operation_name": "GetUserProfileWithPosts",
        "query_hash": "abc123def456ghi789",
        "execution_time_ms": 2340,
        "complexity_score": 45,
        "database_queries": 15,
        "memory_usage_mb": 67,
        "cache_hits": 3,
        "cache_misses": 8,
        "timestamp": "2024-01-15T10:28:30Z",
        "query_text": "query GetUserProfileWithPosts($userId: ID!) { user(id: $userId) { id name email posts { id title content comments { id text author { name } } } } }",
        "variables": {
          "userId": "123"
        },
        "performance_breakdown": {
          "parsing_ms": 5,
          "validation_ms": 12,
          "execution_ms": 2323,
          "database_ms": 1890,
          "cache_ms": 45
        }
      },
      {
        "id": "query_002",
        "operation_name": "SearchProducts",
        "query_hash": "def456ghi789jkl012",
        "execution_time_ms": 1850,
        "complexity_score": 32,
        "database_queries": 8,
        "memory_usage_mb": 42,
        "cache_hits": 12,
        "cache_misses": 2,
        "timestamp": "2024-01-15T10:26:15Z",
        "query_text": "query SearchProducts($filters: ProductFilters!) { products(filters: $filters) { id name price category { name } reviews { rating comment } } }",
        "variables": {
          "filters": {
            "category": "electronics",
            "priceRange": [100, 500]
          }
        },
        "performance_breakdown": {
          "parsing_ms": 3,
          "validation_ms": 8,
          "execution_ms": 1839,
          "database_ms": 1456,
          "cache_ms": 23
        }
      }
    ],
    "pagination": {
      "total": 23,
      "limit": 10,
      "offset": 0,
      "has_next": true
    },
    "summary": {
      "avg_execution_time_ms": 1245.6,
      "slowest_query_ms": 2340,
      "total_slow_queries": 23,
      "threshold_ms": 1000
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid action parameter",
    "details": {
      "parameter": "action",
      "value": "invalid_action",
      "allowed_values": ["stats", "alerts", "slow_queries"]
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 403 Forbidden
```json
{
  "status": "error",
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Insufficient permissions to access performance data"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred while processing the request"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Usage Examples

### Python/Requests

```python
import requests
import json

# Get performance statistics
response = requests.get('http://localhost:8000/graphql/performance/?action=stats')
stats = response.json()
print(f"Average response time: {stats['data']['overview']['avg_response_time_ms']}ms")

# Get recent alerts
response = requests.get('http://localhost:8000/graphql/performance/?action=alerts&limit=5')
alerts = response.json()
for alert in alerts['data']['alerts']:
    print(f"Alert: {alert['message']} - {alert['severity']}")

# Get slow queries with date filter
from datetime import datetime, timedelta
start_date = (datetime.now() - timedelta(hours=24)).isoformat()
response = requests.get(
    f'http://localhost:8000/graphql/performance/?action=slow_queries&start_date={start_date}'
)
slow_queries = response.json()
print(f"Found {len(slow_queries['data']['slow_queries'])} slow queries in last 24 hours")
```

### JavaScript/Fetch

```javascript
// Get performance statistics
async function getPerformanceStats() {
  const response = await fetch('/graphql/performance/?action=stats');
  const data = await response.json();
  
  if (data.status === 'success') {
    console.log('Performance Overview:', data.data.overview);
    return data.data;
  } else {
    console.error('Error:', data.error.message);
  }
}

// Get recent alerts
async function getRecentAlerts(limit = 10) {
  const response = await fetch(`/graphql/performance/?action=alerts&limit=${limit}`);
  const data = await response.json();
  
  return data.data.alerts.filter(alert => !alert.resolved);
}

// Monitor slow queries
async function monitorSlowQueries() {
  const response = await fetch('/graphql/performance/?action=slow_queries&limit=5');
  const data = await response.json();
  
  data.data.slow_queries.forEach(query => {
    if (query.execution_time_ms > 2000) {
      console.warn(`Very slow query detected: ${query.operation_name} (${query.execution_time_ms}ms)`);
    }
  });
}
```

### cURL Examples

```bash
# Get basic performance statistics
curl -X GET "http://localhost:8000/graphql/performance/?action=stats" \
  -H "Accept: application/json"

# Get alerts with pagination
curl -X GET "http://localhost:8000/graphql/performance/?action=alerts&limit=20&offset=0" \
  -H "Accept: application/json"

# Get slow queries from last hour
curl -X GET "http://localhost:8000/graphql/performance/?action=slow_queries&start_date=2024-01-15T09:30:00Z" \
  -H "Accept: application/json"

# Get performance data with authentication
curl -X GET "http://localhost:8000/graphql/performance/?action=stats" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Rate Limiting

Performance API endpoints are subject to rate limiting to prevent abuse:

- **Default limit**: 100 requests per minute per IP
- **Authenticated users**: 500 requests per minute
- **Admin users**: 1000 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## Caching

Performance data is cached to improve response times:

- **Statistics**: Cached for 1 minute
- **Alerts**: Cached for 30 seconds
- **Slow queries**: Cached for 2 minutes

Cache headers indicate freshness:
```
Cache-Control: max-age=60
ETag: "abc123def456"
Last-Modified: Mon, 15 Jan 2024 10:30:00 GMT
```

## Integration Examples

### Monitoring Dashboard

```python
# Django view for performance dashboard
from django.shortcuts import render
import requests

def performance_dashboard(request):
    # Get performance data
    stats_response = requests.get('http://localhost:8000/graphql/performance/?action=stats')
    alerts_response = requests.get('http://localhost:8000/graphql/performance/?action=alerts&limit=10')
    
    context = {
        'stats': stats_response.json()['data'],
        'alerts': alerts_response.json()['data']['alerts'],
    }
    return render(request, 'performance_dashboard.html', context)
```

### Automated Alerting

```python
# Celery task for automated alerting
from celery import shared_task
import requests
from django.core.mail import send_mail

@shared_task
def check_performance_alerts():
    response = requests.get('http://localhost:8000/graphql/performance/?action=alerts&limit=50')
    data = response.json()
    
    unresolved_alerts = [alert for alert in data['data']['alerts'] if not alert['resolved']]
    
    if unresolved_alerts:
        critical_alerts = [alert for alert in unresolved_alerts if alert['severity'] == 'error']
        
        if critical_alerts:
            send_mail(
                'Critical Performance Alerts',
                f'Found {len(critical_alerts)} critical performance issues',
                'noreply@example.com',
                ['admin@example.com'],
            )
```

## Next Steps

- [Performance Metrics Guide](../features/performance-metrics.md)
- [Setup Guide](../setup/performance-setup.md)
- [Troubleshooting](../troubleshooting/performance-troubleshooting.md)
- [Best Practices](../project/performance-best-practices.md)