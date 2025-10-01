# Alerting Configuration

Django GraphQL Auto provides comprehensive alerting capabilities to notify you of issues, performance degradation, and system anomalies in real-time.

## Overview

The alerting system supports:
- Threshold-based alerts
- Anomaly detection
- Custom alert conditions
- Multiple notification channels
- Alert suppression and escalation
- Integration with popular alerting platforms

## Basic Alert Setup

### Enabling Alerts

```python
# settings.py
RAIL_GRAPHQL_ALERTS = {
    'ENABLED': True,
    'DEFAULT_CHANNELS': ['email', 'slack'],
    'ALERT_MANAGER': 'integrated',
    'SUPPRESSION_ENABLED': True,
    'ESCALATION_ENABLED': True,
}
```

### Simple Threshold Alerts

```python
from rail_django_graphql.alerts import ThresholdAlert

# Response time alert
response_time_alert = ThresholdAlert(
    name='high_response_time',
    metric='query_response_time',
    threshold=1000,  # milliseconds
    condition='greater_than',
    severity='warning',
    channels=['email', 'slack']
)

# Error rate alert
error_rate_alert = ThresholdAlert(
    name='high_error_rate',
    metric='error_rate',
    threshold=0.05,  # 5%
    condition='greater_than',
    severity='critical',
    channels=['email', 'slack', 'pagerduty']
)

# Register alerts
from rail_django_graphql.alerts import register_alert
register_alert(response_time_alert)
register_alert(error_rate_alert)
```

## Alert Types

### Performance Alerts

```python
from rail_django_graphql.alerts import PerformanceAlert

# Query complexity alert
complexity_alert = PerformanceAlert(
    name='query_complexity_high',
    metric='query_complexity',
    threshold=500,
    window='5m',
    severity='warning'
)

# Database query count alert
db_query_alert = PerformanceAlert(
    name='excessive_db_queries',
    metric='db_query_count',
    threshold=100,
    per_request=True,
    severity='warning'
)
```

### Health Alerts

```python
from rail_django_graphql.alerts import HealthAlert

# Schema availability alert
schema_alert = HealthAlert(
    name='schema_unavailable',
    check='schema_health',
    condition='unhealthy',
    severity='critical',
    immediate=True
)

# Database connectivity alert
db_health_alert = HealthAlert(
    name='database_connection_failed',
    check='database_health',
    condition='connection_failed',
    severity='critical',
    immediate=True
)
```

### Business Logic Alerts

```python
from rail_django_graphql.alerts import BusinessAlert

# User activity alert
user_activity_alert = BusinessAlert(
    name='low_user_activity',
    metric='active_users_per_hour',
    threshold=10,
    condition='less_than',
    window='1h',
    severity='warning'
)

# Revenue impact alert
revenue_alert = BusinessAlert(
    name='revenue_drop',
    metric='orders_per_minute',
    threshold=5,
    condition='less_than',
    window='10m',
    severity='critical'
)
```

## Custom Alert Conditions

### Advanced Conditions

```python
from rail_django_graphql.alerts import CustomAlert

class AnomalyAlert(CustomAlert):
    def evaluate_condition(self, current_value, historical_data):
        # Calculate z-score for anomaly detection
        mean = sum(historical_data) / len(historical_data)
        variance = sum((x - mean) ** 2 for x in historical_data) / len(historical_data)
        std_dev = variance ** 0.5
        z_score = (current_value - mean) / std_dev
        
        return abs(z_score) > 2.0  # Alert if more than 2 standard deviations

# Trend-based alert
class TrendAlert(CustomAlert):
    def evaluate_condition(self, values):
        # Alert if metric is consistently increasing
        if len(values) < 5:
            return False
        
        increasing_count = 0
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increasing_count += 1
        
        return increasing_count >= 4  # 4 out of 5 increases
```

### Composite Alerts

```python
from rail_django_graphql.alerts import CompositeAlert

# Alert when both response time is high AND error rate is high
composite_alert = CompositeAlert(
    name='performance_degradation',
    conditions=[
        ('query_response_time', 'greater_than', 500),
        ('error_rate', 'greater_than', 0.02)
    ],
    operator='AND',
    severity='critical'
)
```

## Notification Channels

### Email Notifications

```python
from rail_django_graphql.alerts.channels import EmailChannel

email_channel = EmailChannel(
    smtp_host='smtp.gmail.com',
    smtp_port=587,
    username='alerts@yourcompany.com',
    password='your-password',
    from_email='alerts@yourcompany.com',
    to_emails=['team@yourcompany.com', 'oncall@yourcompany.com']
)

# Register email channel
from rail_django_graphql.alerts import register_channel
register_channel('email', email_channel)
```

### Slack Integration

```python
from rail_django_graphql.alerts.channels import SlackChannel

slack_channel = SlackChannel(
    webhook_url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
    channel='#alerts',
    username='GraphQL Alert Bot',
    icon_emoji=':warning:'
)

register_channel('slack', slack_channel)
```

### PagerDuty Integration

```python
from rail_django_graphql.alerts.channels import PagerDutyChannel

pagerduty_channel = PagerDutyChannel(
    integration_key='your-pagerduty-integration-key',
    severity_mapping={
        'critical': 'critical',
        'warning': 'warning',
        'info': 'info'
    }
)

register_channel('pagerduty', pagerduty_channel)
```

### Custom Notification Channels

```python
from rail_django_graphql.alerts.channels import BaseChannel

class TeamsChannel(BaseChannel):
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_notification(self, alert):
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000" if alert.severity == 'critical' else "FFA500",
            "summary": alert.title,
            "sections": [{
                "activityTitle": f"GraphQL Alert: {alert.name}",
                "activitySubtitle": alert.message,
                "facts": [
                    {"name": "Severity", "value": alert.severity},
                    {"name": "Metric", "value": alert.metric},
                    {"name": "Value", "value": str(alert.current_value)},
                    {"name": "Threshold", "value": str(alert.threshold)},
                    {"name": "Time", "value": alert.timestamp.isoformat()}
                ]
            }]
        }
        
        requests.post(self.webhook_url, json=payload)

register_channel('teams', TeamsChannel('your-teams-webhook-url'))
```

## Alert Configuration

### Alert Rules Configuration

```python
# settings.py
RAIL_GRAPHQL_ALERT_RULES = {
    'performance': {
        'response_time_warning': {
            'metric': 'avg_response_time',
            'threshold': 500,
            'condition': 'greater_than',
            'window': '5m',
            'severity': 'warning',
            'channels': ['slack']
        },
        'response_time_critical': {
            'metric': 'avg_response_time',
            'threshold': 1000,
            'condition': 'greater_than',
            'window': '2m',
            'severity': 'critical',
            'channels': ['slack', 'pagerduty']
        }
    },
    'errors': {
        'high_error_rate': {
            'metric': 'error_rate',
            'threshold': 0.05,
            'condition': 'greater_than',
            'window': '3m',
            'severity': 'critical',
            'channels': ['email', 'slack', 'pagerduty']
        }
    },
    'health': {
        'service_down': {
            'metric': 'service_availability',
            'threshold': 1,
            'condition': 'less_than',
            'window': '1m',
            'severity': 'critical',
            'channels': ['pagerduty'],
            'immediate': True
        }
    }
}
```

### Channel Configuration

```python
# settings.py
RAIL_GRAPHQL_ALERT_CHANNELS = {
    'email': {
        'class': 'rail_django_graphql.alerts.channels.EmailChannel',
        'config': {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'alerts@yourcompany.com',
            'password': 'your-app-password',
            'from_email': 'alerts@yourcompany.com',
            'to_emails': ['team@yourcompany.com']
        }
    },
    'slack': {
        'class': 'rail_django_graphql.alerts.channels.SlackChannel',
        'config': {
            'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
            'channel': '#alerts'
        }
    },
    'pagerduty': {
        'class': 'rail_django_graphql.alerts.channels.PagerDutyChannel',
        'config': {
            'integration_key': 'your-pagerduty-integration-key'
        }
    }
}
```

## Alert Suppression

### Time-based Suppression

```python
from rail_django_graphql.alerts import AlertSuppression

# Suppress alerts during maintenance windows
maintenance_suppression = AlertSuppression(
    name='maintenance_window',
    start_time='02:00',
    end_time='04:00',
    timezone='UTC',
    days=['sunday'],
    alerts=['all']
)

# Suppress specific alerts during business hours
business_hours_suppression = AlertSuppression(
    name='business_hours',
    start_time='09:00',
    end_time='17:00',
    timezone='America/New_York',
    days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    alerts=['low_priority_alerts']
)
```

### Condition-based Suppression

```python
from rail_django_graphql.alerts import ConditionalSuppression

# Suppress alerts when system is in maintenance mode
maintenance_suppression = ConditionalSuppression(
    name='maintenance_mode',
    condition=lambda: get_system_status() == 'maintenance',
    alerts=['performance_alerts']
)

# Suppress alerts during deployment
deployment_suppression = ConditionalSuppression(
    name='deployment_active',
    condition=lambda: check_deployment_status(),
    duration=600,  # 10 minutes
    alerts=['availability_alerts']
)
```

## Alert Escalation

### Escalation Policies

```python
from rail_django_graphql.alerts import EscalationPolicy

# Define escalation policy
escalation_policy = EscalationPolicy(
    name='critical_escalation',
    levels=[
        {
            'delay': 0,  # Immediate
            'channels': ['slack'],
            'recipients': ['team-lead@company.com']
        },
        {
            'delay': 300,  # 5 minutes
            'channels': ['email', 'slack'],
            'recipients': ['team@company.com']
        },
        {
            'delay': 900,  # 15 minutes
            'channels': ['pagerduty'],
            'recipients': ['oncall@company.com']
        }
    ]
)

# Apply escalation policy to alerts
critical_alert = ThresholdAlert(
    name='service_down',
    metric='service_availability',
    threshold=1,
    condition='less_than',
    severity='critical',
    escalation_policy=escalation_policy
)
```

## Alert Management API

### REST API

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('api/alerts/', include('rail_django_graphql.alerts.urls')),
]
```

Available endpoints:
- `GET /api/alerts/` - List all alerts
- `POST /api/alerts/` - Create new alert
- `GET /api/alerts/{id}/` - Get alert details
- `PUT /api/alerts/{id}/` - Update alert
- `DELETE /api/alerts/{id}/` - Delete alert
- `POST /api/alerts/{id}/acknowledge/` - Acknowledge alert
- `POST /api/alerts/{id}/resolve/` - Resolve alert

### GraphQL API

```graphql
type Alert {
  id: ID!
  name: String!
  metric: String!
  threshold: Float!
  condition: String!
  severity: String!
  status: String!
  createdAt: DateTime!
  lastTriggered: DateTime
  acknowledgedAt: DateTime
  resolvedAt: DateTime
}

type Query {
  alerts(status: String, severity: String): [Alert!]!
  alert(id: ID!): Alert
}

type Mutation {
  createAlert(input: CreateAlertInput!): Alert!
  updateAlert(id: ID!, input: UpdateAlertInput!): Alert!
  deleteAlert(id: ID!): Boolean!
  acknowledgeAlert(id: ID!): Alert!
  resolveAlert(id: ID!): Alert!
}
```

## Alert Testing

### Testing Alert Conditions

```python
from rail_django_graphql.alerts.testing import AlertTester

# Test alert conditions
tester = AlertTester()

# Simulate high response time
test_result = tester.test_alert(
    alert_name='high_response_time',
    test_data={'query_response_time': 1500}
)

assert test_result.should_trigger == True
assert test_result.severity == 'critical'
```

### Integration Testing

```python
import pytest
from rail_django_graphql.alerts.testing import MockChannel

@pytest.fixture
def mock_slack_channel():
    return MockChannel('slack')

def test_alert_notification(mock_slack_channel):
    # Trigger alert
    alert = ThresholdAlert(
        name='test_alert',
        metric='test_metric',
        threshold=100,
        condition='greater_than',
        channels=['slack']
    )
    
    # Simulate metric exceeding threshold
    alert.evaluate({'test_metric': 150})
    
    # Verify notification was sent
    assert mock_slack_channel.notifications_sent == 1
    assert 'test_alert' in mock_slack_channel.last_notification['text']
```

## Monitoring Alert Performance

### Alert Metrics

```python
from rail_django_graphql.alerts.metrics import AlertMetrics

metrics = AlertMetrics()
alert_stats = metrics.get_alert_statistics(period='24h')

print(f"Total alerts triggered: {alert_stats.total_triggered}")
print(f"Average resolution time: {alert_stats.avg_resolution_time}")
print(f"False positive rate: {alert_stats.false_positive_rate}")
```

### Alert Dashboard

```python
from rail_django_graphql.alerts.dashboard import AlertDashboard

dashboard = AlertDashboard()
dashboard_data = dashboard.get_dashboard_data()

# Dashboard includes:
# - Active alerts
# - Alert trends
# - Channel performance
# - Resolution statistics
```

## Best Practices

### 1. Alert Hierarchy

```python
# Define clear severity levels
SEVERITY_LEVELS = {
    'info': {
        'description': 'Informational, no action required',
        'channels': ['slack'],
        'escalation': False
    },
    'warning': {
        'description': 'Potential issue, monitor closely',
        'channels': ['slack', 'email'],
        'escalation': False
    },
    'critical': {
        'description': 'Immediate action required',
        'channels': ['slack', 'email', 'pagerduty'],
        'escalation': True
    }
}
```

### 2. Meaningful Alert Names

```python
# Good: Descriptive and actionable
high_response_time_alert = ThresholdAlert(
    name='graphql_response_time_above_1s',
    description='GraphQL queries taking longer than 1 second'
)

# Bad: Vague and unclear
bad_alert = ThresholdAlert(
    name='alert1',
    description='Something is wrong'
)
```

### 3. Appropriate Thresholds

```python
# Use percentile-based thresholds
response_time_alert = ThresholdAlert(
    name='high_p95_response_time',
    metric='p95_response_time',
    threshold=800,  # Based on historical data
    window='5m'
)
```

### 4. Alert Fatigue Prevention

```python
# Implement alert suppression
RAIL_GRAPHQL_ALERTS = {
    'SUPPRESSION': {
        'ENABLED': True,
        'COOLDOWN_PERIOD': 300,  # 5 minutes
        'MAX_ALERTS_PER_HOUR': 10,
        'DUPLICATE_SUPPRESSION': True
    }
}
```

## Troubleshooting Alerts

### Common Issues

1. **Alerts Not Triggering**
   ```python
   # Check alert registration
   from rail_django_graphql.alerts import list_registered_alerts
   print(list_registered_alerts())
   
   # Verify metric collection
   from rail_django_graphql.metrics import get_metric_value
   value = get_metric_value('query_response_time')
   print(f"Current metric value: {value}")
   ```

2. **Too Many False Positives**
   ```python
   # Adjust thresholds based on historical data
   from rail_django_graphql.alerts.analysis import ThresholdAnalyzer
   
   analyzer = ThresholdAnalyzer()
   recommended_threshold = analyzer.analyze_metric(
       'query_response_time',
       period='30d',
       false_positive_rate=0.05
   )
   ```

3. **Notification Delivery Issues**
   ```python
   # Test notification channels
   from rail_django_graphql.alerts.testing import test_channel
   
   result = test_channel('slack', test_message='Test alert')
   if not result.success:
       print(f"Channel test failed: {result.error}")
   ```

## See Also

- [Health Checks](health-checks.md)
- [Metrics Documentation](metrics.md)
- [Monitoring Guide](monitoring.md)
- [Performance Optimization](../development/performance.md)
- [Troubleshooting Guide](../development/troubleshooting.md)