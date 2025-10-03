#!/usr/bin/env python3
"""
Health Check Script for Django GraphQL Auto System

This script performs comprehensive health checks on all system components
and provides detailed status information for monitoring and alerting.

Usage:
    python health-check.py [--component COMPONENT] [--format FORMAT] [--timeout TIMEOUT]

Components:
    - django: Django application health
    - database: PostgreSQL database connectivity
    - redis: Redis cache connectivity
    - nginx: Nginx web server status
    - ssl: SSL certificate validation
    - disk: Disk space monitoring
    - memory: Memory usage monitoring
    - all: All components (default)

Formats:
    - json: JSON output for programmatic use
    - text: Human-readable text output
    - prometheus: Prometheus metrics format
"""

import argparse
import json
import logging
import os
import psutil
import redis
import requests
import ssl
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import psycopg2
from psycopg2 import OperationalError

# Configuration
DEFAULT_TIMEOUT = 10
HEALTH_CHECK_CONFIG = {
    'django': {
        'url': os.getenv('DJANGO_HEALTH_URL', 'http://localhost:8000/health/'),
        'timeout': int(os.getenv('DJANGO_HEALTH_TIMEOUT', '10'))
    },
    'database': {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'name': os.getenv('DB_NAME', 'django_graphql'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'timeout': int(os.getenv('DB_HEALTH_TIMEOUT', '5'))
    },
    'redis': {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'password': os.getenv('REDIS_PASSWORD', None),
        'timeout': int(os.getenv('REDIS_HEALTH_TIMEOUT', '5'))
    },
    'nginx': {
        'url': os.getenv('NGINX_STATUS_URL', 'http://localhost/nginx_status'),
        'timeout': int(os.getenv('NGINX_HEALTH_TIMEOUT', '5'))
    },
    'ssl': {
        'domains': os.getenv('SSL_DOMAINS', 'localhost').split(','),
        'warning_days': int(os.getenv('SSL_WARNING_DAYS', '30'))
    },
    'thresholds': {
        'disk_usage_warning': float(os.getenv('DISK_WARNING_THRESHOLD', '80')),
        'disk_usage_critical': float(os.getenv('DISK_CRITICAL_THRESHOLD', '90')),
        'memory_usage_warning': float(os.getenv('MEMORY_WARNING_THRESHOLD', '80')),
        'memory_usage_critical': float(os.getenv('MEMORY_CRITICAL_THRESHOLD', '90')),
        'load_warning': float(os.getenv('LOAD_WARNING_THRESHOLD', '2.0')),
        'load_critical': float(os.getenv('LOAD_CRITICAL_THRESHOLD', '4.0'))
    }
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthChecker:
    """Main health checker class"""
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.results = {}
        
    def check_django_health(self) -> Dict:
        """Check Django application health"""
        try:
            url = HEALTH_CHECK_CONFIG['django']['url']
            timeout = HEALTH_CHECK_CONFIG['django']['timeout']
            
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'status': HealthStatus.HEALTHY,
                        'response_time': response.elapsed.total_seconds(),
                        'details': data,
                        'message': 'Django application is healthy'
                    }
                except json.JSONDecodeError:
                    return {
                        'status': HealthStatus.WARNING,
                        'response_time': response.elapsed.total_seconds(),
                        'message': 'Django responded but returned invalid JSON'
                    }
            else:
                return {
                    'status': HealthStatus.CRITICAL,
                    'response_time': response.elapsed.total_seconds(),
                    'message': f'Django returned status code {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Django health check timed out after {timeout}s'
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': HealthStatus.CRITICAL,
                'message': 'Cannot connect to Django application'
            }
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Django health check failed: {str(e)}'
            }
    
    def check_database_health(self) -> Dict:
        """Check PostgreSQL database health"""
        try:
            config = HEALTH_CHECK_CONFIG['database']
            
            start_time = time.time()
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['name'],
                user=config['user'],
                password=config['password'],
                connect_timeout=config['timeout']
            )
            
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            
            # Check database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            db_size = cursor.fetchone()[0]
            
            # Check active connections
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            response_time = time.time() - start_time
            
            return {
                'status': HealthStatus.HEALTHY,
                'response_time': response_time,
                'details': {
                    'version': version,
                    'database_size': db_size,
                    'active_connections': active_connections
                },
                'message': 'Database is healthy'
            }
            
        except OperationalError as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Database connection failed: {str(e)}'
            }
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Database health check failed: {str(e)}'
            }
    
    def check_redis_health(self) -> Dict:
        """Check Redis cache health"""
        try:
            config = HEALTH_CHECK_CONFIG['redis']
            
            start_time = time.time()
            r = redis.Redis(
                host=config['host'],
                port=config['port'],
                db=config['db'],
                password=config['password'],
                socket_timeout=config['timeout']
            )
            
            # Test connection
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            response_time = time.time() - start_time
            
            return {
                'status': HealthStatus.HEALTHY,
                'response_time': response_time,
                'details': {
                    'version': info.get('redis_version'),
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'uptime_in_seconds': info.get('uptime_in_seconds')
                },
                'message': 'Redis is healthy'
            }
            
        except redis.exceptions.ConnectionError:
            return {
                'status': HealthStatus.CRITICAL,
                'message': 'Cannot connect to Redis'
            }
        except redis.exceptions.TimeoutError:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Redis connection timed out after {config["timeout"]}s'
            }
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Redis health check failed: {str(e)}'
            }
    
    def check_nginx_health(self) -> Dict:
        """Check Nginx web server health"""
        try:
            config = HEALTH_CHECK_CONFIG['nginx']
            
            response = requests.get(config['url'], timeout=config['timeout'])
            
            if response.status_code == 200:
                return {
                    'status': HealthStatus.HEALTHY,
                    'response_time': response.elapsed.total_seconds(),
                    'message': 'Nginx is healthy'
                }
            else:
                return {
                    'status': HealthStatus.WARNING,
                    'response_time': response.elapsed.total_seconds(),
                    'message': f'Nginx returned status code {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': HealthStatus.CRITICAL,
                'message': 'Cannot connect to Nginx'
            }
        except Exception as e:
            return {
                'status': HealthStatus.WARNING,
                'message': f'Nginx health check failed: {str(e)}'
            }
    
    def check_ssl_certificates(self) -> Dict:
        """Check SSL certificate expiration"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for domain in HEALTH_CHECK_CONFIG['ssl']['domains']:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        
                        # Parse expiration date
                        expiry_date = datetime.strptime(
                            cert['notAfter'], '%b %d %H:%M:%S %Y %Z'
                        )
                        
                        days_until_expiry = (expiry_date - datetime.now()).days
                        warning_days = HEALTH_CHECK_CONFIG['ssl']['warning_days']
                        
                        if days_until_expiry < 0:
                            status = HealthStatus.CRITICAL
                            message = f'Certificate expired {abs(days_until_expiry)} days ago'
                        elif days_until_expiry < warning_days:
                            status = HealthStatus.WARNING
                            message = f'Certificate expires in {days_until_expiry} days'
                        else:
                            status = HealthStatus.HEALTHY
                            message = f'Certificate valid for {days_until_expiry} days'
                        
                        results[domain] = {
                            'status': status,
                            'expiry_date': expiry_date.isoformat(),
                            'days_until_expiry': days_until_expiry,
                            'message': message
                        }
                        
                        if status == HealthStatus.CRITICAL:
                            overall_status = HealthStatus.CRITICAL
                        elif status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                            overall_status = HealthStatus.WARNING
                            
            except Exception as e:
                results[domain] = {
                    'status': HealthStatus.CRITICAL,
                    'message': f'SSL check failed: {str(e)}'
                }
                overall_status = HealthStatus.CRITICAL
        
        return {
            'status': overall_status,
            'details': results,
            'message': f'Checked {len(results)} SSL certificates'
        }
    
    def check_disk_usage(self) -> Dict:
        """Check disk space usage"""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            thresholds = HEALTH_CHECK_CONFIG['thresholds']
            
            if usage_percent >= thresholds['disk_usage_critical']:
                status = HealthStatus.CRITICAL
                message = f'Disk usage critical: {usage_percent:.1f}%'
            elif usage_percent >= thresholds['disk_usage_warning']:
                status = HealthStatus.WARNING
                message = f'Disk usage warning: {usage_percent:.1f}%'
            else:
                status = HealthStatus.HEALTHY
                message = f'Disk usage normal: {usage_percent:.1f}%'
            
            return {
                'status': status,
                'details': {
                    'total': disk_usage.total,
                    'used': disk_usage.used,
                    'free': disk_usage.free,
                    'percent': usage_percent
                },
                'message': message
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Disk usage check failed: {str(e)}'
            }
    
    def check_memory_usage(self) -> Dict:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            thresholds = HEALTH_CHECK_CONFIG['thresholds']
            
            if usage_percent >= thresholds['memory_usage_critical']:
                status = HealthStatus.CRITICAL
                message = f'Memory usage critical: {usage_percent:.1f}%'
            elif usage_percent >= thresholds['memory_usage_warning']:
                status = HealthStatus.WARNING
                message = f'Memory usage warning: {usage_percent:.1f}%'
            else:
                status = HealthStatus.HEALTHY
                message = f'Memory usage normal: {usage_percent:.1f}%'
            
            return {
                'status': status,
                'details': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': usage_percent
                },
                'message': message
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Memory usage check failed: {str(e)}'
            }
    
    def run_health_checks(self, components: List[str]) -> Dict:
        """Run health checks for specified components"""
        check_methods = {
            'django': self.check_django_health,
            'database': self.check_database_health,
            'redis': self.check_redis_health,
            'nginx': self.check_nginx_health,
            'ssl': self.check_ssl_certificates,
            'disk': self.check_disk_usage,
            'memory': self.check_memory_usage
        }
        
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for component in components:
            if component in check_methods:
                logger.info(f"Checking {component} health...")
                result = check_methods[component]()
                results[component] = result
                
                # Update overall status
                if result['status'] == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif result['status'] == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.WARNING
            else:
                logger.warning(f"Unknown component: {component}")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'components': results
        }


def format_output(results: Dict, format_type: str) -> str:
    """Format health check results"""
    if format_type == 'json':
        return json.dumps(results, indent=2)
    
    elif format_type == 'prometheus':
        metrics = []
        
        # Overall health metric
        status_values = {
            HealthStatus.HEALTHY: 1,
            HealthStatus.WARNING: 0.5,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: -1
        }
        
        overall_value = status_values.get(results['overall_status'], -1)
        metrics.append(f'health_check_overall_status {overall_value}')
        
        # Component-specific metrics
        for component, result in results['components'].items():
            component_value = status_values.get(result['status'], -1)
            metrics.append(f'health_check_component_status{{component="{component}"}} {component_value}')
            
            if 'response_time' in result:
                metrics.append(f'health_check_response_time_seconds{{component="{component}"}} {result["response_time"]}')
        
        return '\n'.join(metrics)
    
    else:  # text format
        output = []
        output.append(f"Health Check Report - {results['timestamp']}")
        output.append("=" * 50)
        output.append(f"Overall Status: {results['overall_status'].upper()}")
        output.append("")
        
        for component, result in results['components'].items():
            output.append(f"{component.upper()}:")
            output.append(f"  Status: {result['status']}")
            output.append(f"  Message: {result['message']}")
            
            if 'response_time' in result:
                output.append(f"  Response Time: {result['response_time']:.3f}s")
            
            if 'details' in result:
                output.append("  Details:")
                for key, value in result['details'].items():
                    output.append(f"    {key}: {value}")
            
            output.append("")
        
        return '\n'.join(output)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Health check script for Django GraphQL Auto System'
    )
    
    parser.add_argument(
        '--component',
        choices=['django', 'database', 'redis', 'nginx', 'ssl', 'disk', 'memory', 'all'],
        default='all',
        help='Component to check (default: all)'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'text', 'prometheus'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f'Timeout in seconds (default: {DEFAULT_TIMEOUT})'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine components to check
    if args.component == 'all':
        components = ['django', 'database', 'redis', 'nginx', 'ssl', 'disk', 'memory']
    else:
        components = [args.component]
    
    # Run health checks
    checker = HealthChecker(timeout=args.timeout)
    results = checker.run_health_checks(components)
    
    # Output results
    output = format_output(results, args.format)
    print(output)
    
    # Exit with appropriate code
    if results['overall_status'] == HealthStatus.CRITICAL:
        sys.exit(2)
    elif results['overall_status'] == HealthStatus.WARNING:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()