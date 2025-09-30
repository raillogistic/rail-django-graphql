# Health System API Reference

## 🔌 REST API Endpoints

### Health Check Endpoints

#### `GET /health/check/`

Simple health check endpoint for load balancers and monitoring tools.

**Response:**

- **200 OK**: System is healthy
- **503 Service Unavailable**: System has issues

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /health/ping/`

Minimal ping endpoint for basic connectivity testing.

**Response:**

```json
{
  "message": "pong",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /health/status/`

Basic status information without detailed metrics.

**Response:**

```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "cache": "healthy",
    "schema": "healthy"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Detailed Health Endpoints

#### `GET /health/api/`

Complete health information including all components and metrics.

**Response:**

```json
{
  "health_status": {
    "overall_status": "healthy",
    "healthy_components": 3,
    "degraded_components": 0,
    "unhealthy_components": 0,
    "recommendations": [],
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "system_metrics": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 67.8,
    "memory_used_mb": 1024.5,
    "memory_available_mb": 487.3,
    "disk_usage_percent": 34.1,
    "active_connections": 12,
    "cache_hit_rate": 0.95,
    "uptime_seconds": 86400
  },
  "components": [
    {
      "component": "GraphQL Schema",
      "status": "healthy",
      "message": "Schema built successfully",
      "response_time_ms": 45.2,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "component": "Database",
      "status": "healthy",
      "message": "Connection successful",
      "response_time_ms": 12.8,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "component": "Cache",
      "status": "healthy",
      "message": "Operations successful",
      "response_time_ms": 3.1,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### `GET /health/metrics/`

System metrics only, without component health details.

**Response:**

```json
{
  "cpu_usage_percent": 45.2,
  "memory_usage_percent": 67.8,
  "memory_used_mb": 1024.5,
  "memory_available_mb": 487.3,
  "disk_usage_percent": 34.1,
  "active_connections": 12,
  "cache_hit_rate": 0.95,
  "uptime_seconds": 86400,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /health/components/`

Component health status without system metrics.

**Response:**

```json
{
  "components": [
    {
      "component": "GraphQL Schema",
      "status": "healthy",
      "message": "Schema built successfully",
      "response_time_ms": 45.2,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "component": "Database",
      "status": "healthy",
      "message": "Connection successful",
      "response_time_ms": 12.8,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "component": "Cache",
      "status": "healthy",
      "message": "Operations successful",
      "response_time_ms": 3.1,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "summary": {
    "healthy": 3,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

### Specialized Health Endpoints

#### `GET /health/schema/`

GraphQL schema-specific health check.

**Response:**

```json
{
  "component": "GraphQL Schema",
  "status": "healthy",
  "message": "Schema built successfully",
  "response_time_ms": 45.2,
  "details": {
    "types_count": 156,
    "queries_count": 23,
    "mutations_count": 18,
    "last_build_time": "2024-01-15T09:15:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /health/database/`

Database-specific health check.

**Response:**

```json
{
  "component": "Database",
  "status": "healthy",
  "message": "Connection successful",
  "response_time_ms": 12.8,
  "details": {
    "connection_pool_size": 20,
    "active_connections": 5,
    "idle_connections": 15,
    "database_size_mb": 2048.7
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /health/cache/`

Cache system-specific health check.

**Response:**

```json
{
  "component": "Cache",
  "status": "healthy",
  "message": "Operations successful",
  "response_time_ms": 3.1,
  "details": {
    "hit_rate": 0.95,
    "miss_rate": 0.05,
    "total_keys": 1247,
    "memory_usage_mb": 128.4
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Historical Data Endpoints

#### `GET /health/history/`

Historical health data for trend analysis.

**Query Parameters:**

- `hours` (optional): Number of hours of history to retrieve (default: 24)
- `component` (optional): Filter by specific component name

**Response:**

```json
{
  "timeframe": "24 hours",
  "data_points": 24,
  "history": [
    {
      "timestamp": "2024-01-15T09:30:00Z",
      "overall_status": "healthy",
      "cpu_usage": 42.1,
      "memory_usage": 65.3,
      "response_times": {
        "schema": 43.2,
        "database": 11.5,
        "cache": 2.8
      }
    },
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "overall_status": "healthy",
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "response_times": {
        "schema": 45.2,
        "database": 12.8,
        "cache": 3.1
      }
    }
  ]
}
```

## 🔍 GraphQL API

### Health Queries

#### Basic Health Query

```graphql
query {
  healthStatus {
    overallStatus
    healthyComponents
    degradedComponents
    unhealthyComponents
    recommendations
    timestamp
  }
}
```

**Response:**

```json
{
  "data": {
    "healthStatus": {
      "overallStatus": "healthy",
      "healthyComponents": 3,
      "degradedComponents": 0,
      "unhealthyComponents": 0,
      "recommendations": [],
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

#### System Metrics Query

```graphql
query {
  systemMetrics {
    cpuUsagePercent
    memoryUsagePercent
    memoryUsedMb
    memoryAvailableMb
    diskUsagePercent
    activeConnections
    cacheHitRate
    uptimeSeconds
  }
}
```

**Response:**

```json
{
  "data": {
    "systemMetrics": {
      "cpuUsagePercent": 45.2,
      "memoryUsagePercent": 67.8,
      "memoryUsedMb": 1024.5,
      "memoryAvailableMb": 487.3,
      "diskUsagePercent": 34.1,
      "activeConnections": 12,
      "cacheHitRate": 0.95,
      "uptimeSeconds": 86400
    }
  }
}
```

#### Complete Health Report Query

```graphql
query {
  healthReport {
    healthStatus {
      overallStatus
      healthyComponents
      degradedComponents
      unhealthyComponents
      recommendations
      timestamp
    }
    systemMetrics {
      cpuUsagePercent
      memoryUsagePercent
      memoryUsedMb
      memoryAvailableMb
      diskUsagePercent
      activeConnections
      cacheHitRate
      uptimeSeconds
    }
    componentDetails {
      component
      status
      message
      responseTimeMs
      timestamp
    }
  }
}
```

### GraphQL Schema Types

#### HealthStatusType

```graphql
type HealthStatusType {
  overallStatus: String!
  healthyComponents: Int!
  degradedComponents: Int!
  unhealthyComponents: Int!
  recommendations: [String!]!
  timestamp: String!
}
```

#### SystemMetricsType

```graphql
type SystemMetricsType {
  cpuUsagePercent: Float!
  memoryUsagePercent: Float!
  memoryUsedMb: Float!
  memoryAvailableMb: Float!
  diskUsagePercent: Float!
  activeConnections: Int!
  cacheHitRate: Float!
  uptimeSeconds: Int!
}
```

#### ComponentHealthType

```graphql
type ComponentHealthType {
  component: String!
  status: String!
  message: String!
  responseTimeMs: Float!
  timestamp: String!
}
```

#### HealthReportType

```graphql
type HealthReportType {
  healthStatus: HealthStatusType!
  systemMetrics: SystemMetricsType!
  componentDetails: [ComponentHealthType!]!
}
```

## 🔧 Python API

### HealthChecker Class

#### Initialization

```python
from rail_django_graphql.extensions.health import HealthChecker

# Initialize with default settings
checker = HealthChecker()

# Initialize with custom cache timeout
checker = HealthChecker(cache_timeout=600)  # 10 minutes
```

#### Methods

##### `get_health_status() -> HealthStatus`

Get overall system health status.

```python
status = checker.get_health_status()
print(f"Overall status: {status.overall_status}")
print(f"Healthy components: {status.healthy_components}")
print(f"Recommendations: {status.recommendations}")
```

##### `get_system_metrics() -> SystemMetrics`

Get current system performance metrics.

```python
metrics = checker.get_system_metrics()
print(f"CPU usage: {metrics.cpu_usage_percent}%")
print(f"Memory usage: {metrics.memory_usage_percent}%")
print(f"Cache hit rate: {metrics.cache_hit_rate}")
```

##### `check_schema_health() -> dict`

Check GraphQL schema health specifically.

```python
schema_health = checker.check_schema_health()
print(f"Schema status: {schema_health['status']}")
print(f"Response time: {schema_health['response_time_ms']}ms")
```

##### `check_database_health() -> dict`

Check database connectivity and performance.

```python
db_health = checker.check_database_health()
print(f"Database status: {db_health['status']}")
print(f"Response time: {db_health['response_time_ms']}ms")
```

##### `check_cache_health() -> dict`

Check cache system health and performance.

```python
cache_health = checker.check_cache_health()
print(f"Cache status: {cache_health['status']}")
print(f"Response time: {cache_health['response_time_ms']}ms")
```

##### `get_health_report() -> dict`

Get complete health report with all components and metrics.

```python
report = checker.get_health_report()
print(f"Overall status: {report['health_status']['overall_status']}")
print(f"CPU usage: {report['system_metrics']['cpu_usage_percent']}%")
for component in report['component_details']:
    print(f"{component['component']}: {component['status']}")
```

### Data Classes

#### HealthStatus

```python
@dataclass
class HealthStatus:
    overall_status: str          # "healthy", "degraded", "unhealthy"
    healthy_components: int      # Number of healthy components
    degraded_components: int     # Number of degraded components
    unhealthy_components: int    # Number of unhealthy components
    recommendations: List[str]   # List of recommendations
    timestamp: str              # ISO format timestamp
```

#### SystemMetrics

```python
@dataclass
class SystemMetrics:
    cpu_usage_percent: float     # CPU usage percentage
    memory_usage_percent: float  # Memory usage percentage
    memory_used_mb: float       # Used memory in MB
    memory_available_mb: float  # Available memory in MB
    disk_usage_percent: float   # Disk usage percentage
    active_connections: int     # Active database connections
    cache_hit_rate: float      # Cache hit rate (0.0 to 1.0)
    uptime_seconds: int        # System uptime in seconds
```

## 🚨 Error Responses

### HTTP Error Codes

#### 503 Service Unavailable

Returned when the system is unhealthy.

```json
{
  "status": "unhealthy",
  "error": "System health check failed",
  "details": {
    "unhealthy_components": ["Database", "Cache"],
    "error_messages": [
      "Database connection timeout",
      "Cache service unavailable"
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 500 Internal Server Error

Returned when the health check system itself fails.

```json
{
  "status": "error",
  "error": "Health check system failure",
  "message": "Unable to perform health checks",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GraphQL Errors

#### Health Check Failure

```json
{
  "data": null,
  "errors": [
    {
      "message": "Health check failed: Database connection timeout",
      "locations": [{ "line": 2, "column": 3 }],
      "path": ["healthStatus"]
    }
  ]
}
```

## 📊 Status Values

### Overall Status

- **`healthy`**: All components are functioning normally
- **`degraded`**: Some components have performance issues but are functional
- **`unhealthy`**: One or more critical components are failing

### Component Status

- **`healthy`**: Component is functioning normally
- **`degraded`**: Component has performance issues but is functional
- **`unhealthy`**: Component is failing or unavailable

### Response Time Thresholds

- **Healthy**: < 100ms
- **Degraded**: 100ms - 1000ms
- **Unhealthy**: > 1000ms or timeout

## 🔄 Caching Behavior

### Cache Keys

- `health_check:status` - Overall health status
- `health_check:metrics` - System metrics
- `health_check:schema` - Schema health
- `health_check:database` - Database health
- `health_check:cache` - Cache health

### Cache Timeouts

- **Default**: 300 seconds (5 minutes)
- **Configurable**: Via `HEALTH_CHECK_SETTINGS['CACHE_TIMEOUT']`
- **Manual Invalidation**: Available via admin interface

### Cache Invalidation

Cache is automatically invalidated when:

- System status changes (healthy ↔ degraded ↔ unhealthy)
- Component status changes
- Manual refresh is requested
- Cache timeout expires

## 🔐 Security Considerations

### Access Control

- Health endpoints are publicly accessible by default
- Sensitive system information is excluded from public endpoints
- Detailed metrics may require authentication in production

### Rate Limiting

- Implement rate limiting for health endpoints in production
- Consider caching to reduce system load from frequent health checks
- Monitor for abuse of health check endpoints

### Information Disclosure

- Avoid exposing sensitive system information
- Filter error messages in production environments
- Consider separate internal/external health endpoints

---

**This API reference provides comprehensive documentation for integrating with the Health Checks & Diagnostics system programmatically.**
