Production Deployment
===================

This guide covers deploying Django GraphQL Auto applications to production environments.

.. contents:: Table of Contents
   :local:
   :depth: 2

Production Readiness Checklist
------------------------------

Security Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings/production.py
   import os
   from .base import *

   # Security settings
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
   
   # HTTPS settings
   SECURE_SSL_REDIRECT = True
   SECURE_HSTS_SECONDS = 31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   SECURE_BROWSER_XSS_FILTER = True
   
   # Session security
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   
   # GraphQL specific security
   GRAPHQL_AUTO = {
       'ENABLE_GRAPHIQL': False,  # Disable in production
       'ENABLE_PLAYGROUND': False,
       'MAX_QUERY_COMPLEXITY': 1000,
       'MAX_QUERY_DEPTH': 10,
       'ENABLE_INTROSPECTION': False,  # Disable introspection
   }

Database Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # PostgreSQL production configuration
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('DB_NAME'),
           'USER': os.environ.get('DB_USER'),
           'PASSWORD': os.environ.get('DB_PASSWORD'),
           'HOST': os.environ.get('DB_HOST', 'localhost'),
           'PORT': os.environ.get('DB_PORT', '5432'),
           'CONN_MAX_AGE': 600,
           'OPTIONS': {
               'MAX_CONNS': 20,
               'sslmode': 'require',
           },
       }
   }

Caching Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Redis caching
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
               'CONNECTION_POOL_KWARGS': {
                   'max_connections': 50,
                   'retry_on_timeout': True,
               }
           }
       }
   }
   
   # GraphQL query caching
   GRAPHQL_AUTO = {
       'ENABLE_QUERY_CACHING': True,
       'CACHE_TIMEOUT': 300,  # 5 minutes
       'CACHE_KEY_PREFIX': 'graphql_auto',
   }

Logging Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'verbose': {
               'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
               'style': '{',
           },
           'json': {
               'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
           },
       },
       'handlers': {
           'file': {
               'level': 'INFO',
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': '/var/log/django/app.log',
               'maxBytes': 1024*1024*15,  # 15MB
               'backupCount': 10,
               'formatter': 'json',
           },
           'error_file': {
               'level': 'ERROR',
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': '/var/log/django/error.log',
               'maxBytes': 1024*1024*15,  # 15MB
               'backupCount': 10,
               'formatter': 'json',
           },
       },
       'loggers': {
           'django': {
               'handlers': ['file'],
               'level': 'INFO',
               'propagate': True,
           },
           'rail_django_graphql': {
               'handlers': ['file', 'error_file'],
               'level': 'INFO',
               'propagate': True,
           },
       },
   }

Web Server Configuration
-----------------------

Gunicorn Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # gunicorn.conf.py
   import multiprocessing

   bind = "0.0.0.0:8000"
   workers = multiprocessing.cpu_count() * 2 + 1
   worker_class = "gevent"
   worker_connections = 1000
   max_requests = 1000
   max_requests_jitter = 100
   timeout = 30
   keepalive = 5
   
   # Logging
   accesslog = "/var/log/gunicorn/access.log"
   errorlog = "/var/log/gunicorn/error.log"
   loglevel = "info"
   
   # Process naming
   proc_name = "django_graphql_auto"
   
   # Server mechanics
   daemon = False
   pidfile = "/var/run/gunicorn/django_graphql_auto.pid"
   user = "www-data"
   group = "www-data"
   tmp_upload_dir = None
   
   # SSL (if terminating SSL at Gunicorn)
   # keyfile = "/path/to/keyfile"
   # certfile = "/path/to/certfile"

Nginx Configuration
~~~~~~~~~~~~~~~~~

.. code-block:: nginx

   # /etc/nginx/sites-available/django_graphql_auto
   upstream django_app {
       server 127.0.0.1:8000;
   }
   
   server {
       listen 80;
       server_name your-domain.com www.your-domain.com;
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name your-domain.com www.your-domain.com;
       
       # SSL configuration
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
       ssl_prefer_server_ciphers off;
       
       # Security headers
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
       add_header X-Content-Type-Options nosniff;
       add_header X-Frame-Options DENY;
       add_header X-XSS-Protection "1; mode=block";
       
       # Static files
       location /static/ {
           alias /var/www/django_graphql_auto/static/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
       
       location /media/ {
           alias /var/www/django_graphql_auto/media/;
           expires 1y;
           add_header Cache-Control "public";
       }
       
       # GraphQL endpoint
       location /graphql/ {
           proxy_pass http://django_app;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           
           # WebSocket support (if using subscriptions)
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           
           # Timeouts
           proxy_connect_timeout 60s;
           proxy_send_timeout 60s;
           proxy_read_timeout 60s;
       }
       
       # Health check endpoint
       location /health/ {
           proxy_pass http://django_app;
           proxy_set_header Host $host;
           access_log off;
       }
       
       # Main application
       location / {
           proxy_pass http://django_app;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }

Environment Variables
--------------------

Production Environment File
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # .env.production
   DJANGO_SETTINGS_MODULE=myproject.settings.production
   SECRET_KEY=your-super-secret-key-here
   
   # Database
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   DB_PORT=5432
   
   # Cache
   REDIS_URL=redis://your-redis-host:6379/1
   
   # Email
   EMAIL_HOST=smtp.your-provider.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@domain.com
   EMAIL_HOST_PASSWORD=your-email-password
   
   # External services
   SENTRY_DSN=https://your-sentry-dsn
   
   # GraphQL specific
   GRAPHQL_MAX_QUERY_COMPLEXITY=1000
   GRAPHQL_MAX_QUERY_DEPTH=10

Systemd Service Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   # /etc/systemd/system/django-graphql-auto.service
   [Unit]
   Description=Django GraphQL Auto Gunicorn daemon
   After=network.target
   
   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/django_graphql_auto
   ExecStart=/var/www/django_graphql_auto/venv/bin/gunicorn \
             --config /var/www/django_graphql_auto/gunicorn.conf.py \
             myproject.wsgi:application
   ExecReload=/bin/kill -s HUP $MAINPID
   Restart=on-failure
   RestartSec=5
   
   [Install]
   WantedBy=multi-user.target

Deployment Strategies
--------------------

Blue-Green Deployment
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # deploy.sh
   
   # Configuration
   APP_NAME="django-graphql-auto"
   BLUE_PORT=8000
   GREEN_PORT=8001
   NGINX_CONFIG="/etc/nginx/sites-available/$APP_NAME"
   
   # Determine current environment
   CURRENT_PORT=$(grep -o "127.0.0.1:[0-9]*" $NGINX_CONFIG | cut -d: -f2)
   
   if [ "$CURRENT_PORT" = "$BLUE_PORT" ]; then
       NEW_PORT=$GREEN_PORT
       NEW_ENV="green"
       OLD_ENV="blue"
   else
       NEW_PORT=$BLUE_PORT
       NEW_ENV="blue"
       OLD_ENV="green"
   fi
   
   echo "Deploying to $NEW_ENV environment (port $NEW_PORT)"
   
   # Deploy new version
   cd /var/www/$APP_NAME-$NEW_ENV
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   
   # Start new environment
   gunicorn --bind 127.0.0.1:$NEW_PORT --daemon myproject.wsgi:application
   
   # Health check
   sleep 5
   if curl -f http://127.0.0.1:$NEW_PORT/health/; then
       echo "Health check passed, switching traffic"
       
       # Update Nginx configuration
       sed -i "s/127.0.0.1:$CURRENT_PORT/127.0.0.1:$NEW_PORT/" $NGINX_CONFIG
       nginx -s reload
       
       # Stop old environment
       pkill -f "gunicorn.*$CURRENT_PORT"
       
       echo "Deployment successful"
   else
       echo "Health check failed, rolling back"
       pkill -f "gunicorn.*$NEW_PORT"
       exit 1
   fi

Rolling Deployment
~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # rolling_deploy.sh
   
   SERVERS=("server1.example.com" "server2.example.com" "server3.example.com")
   
   for server in "${SERVERS[@]}"; do
       echo "Deploying to $server"
       
       # Remove from load balancer
       ssh $server "sudo nginx -s stop"
       
       # Deploy
       ssh $server "cd /var/www/django_graphql_auto && \
                    git pull origin main && \
                    source venv/bin/activate && \
                    pip install -r requirements.txt && \
                    python manage.py migrate && \
                    python manage.py collectstatic --noinput && \
                    sudo systemctl restart django-graphql-auto"
       
       # Health check
       sleep 10
       if ssh $server "curl -f http://localhost:8000/health/"; then
           # Add back to load balancer
           ssh $server "sudo nginx -s start"
           echo "Successfully deployed to $server"
       else
           echo "Deployment failed on $server"
           exit 1
       fi
       
       # Wait before next server
       sleep 30
   done

Monitoring and Alerting
----------------------

Health Checks
~~~~~~~~~~~~

.. code-block:: python

   # health/views.py
   from django.http import JsonResponse
   from django.db import connection
   from django.core.cache import cache
   import redis
   
   def health_check(request):
       checks = {
           'database': check_database(),
           'cache': check_cache(),
           'graphql': check_graphql_schema(),
       }
       
       all_healthy = all(checks.values())
       status_code = 200 if all_healthy else 503
       
       return JsonResponse({
           'status': 'healthy' if all_healthy else 'unhealthy',
           'checks': checks,
       }, status=status_code)
   
   def check_database():
       try:
           with connection.cursor() as cursor:
               cursor.execute("SELECT 1")
           return True
       except Exception:
           return False
   
   def check_cache():
       try:
           cache.set('health_check', 'ok', 10)
           return cache.get('health_check') == 'ok'
       except Exception:
           return False
   
   def check_graphql_schema():
       try:
           from rail_django_graphql.schema import schema
           return schema is not None
       except Exception:
           return False

Application Metrics
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # metrics/middleware.py
   import time
   import logging
   from django.core.cache import cache
   
   logger = logging.getLogger(__name__)
   
   class GraphQLMetricsMiddleware:
       def __init__(self, get_response):
           self.get_response = get_response
   
       def __call__(self, request):
           if request.path.startswith('/graphql'):
               start_time = time.time()
               
               response = self.get_response(request)
               
               duration = time.time() - start_time
               
               # Log metrics
               logger.info(f"GraphQL request completed", extra={
                   'duration': duration,
                   'status_code': response.status_code,
                   'user_id': getattr(request.user, 'id', None),
               })
               
               # Update counters
               cache.set('graphql_request_count', 
                        cache.get('graphql_request_count', 0) + 1, 
                        timeout=None)
               
               return response
           
           return self.get_response(request)

Performance Optimization
-----------------------

Database Optimization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Database connection pooling
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'OPTIONS': {
               'MAX_CONNS': 20,
               'MIN_CONNS': 5,
           },
           'CONN_MAX_AGE': 600,
       }
   }
   
   # Query optimization
   GRAPHQL_AUTO = {
       'ENABLE_DATALOADER': True,
       'DATALOADER_CACHE_SIZE': 1000,
       'ENABLE_QUERY_BATCHING': True,
   }

CDN Configuration
~~~~~~~~~~~~~~~

.. code-block:: python

   # Static files CDN
   STATIC_URL = 'https://cdn.your-domain.com/static/'
   MEDIA_URL = 'https://cdn.your-domain.com/media/'
   
   # CloudFront configuration
   AWS_S3_CUSTOM_DOMAIN = 'cdn.your-domain.com'
   AWS_S3_OBJECT_PARAMETERS = {
       'CacheControl': 'max-age=86400',
   }

Backup and Recovery
------------------

Database Backups
~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # backup.sh
   
   BACKUP_DIR="/var/backups/postgresql"
   DATE=$(date +%Y%m%d_%H%M%S)
   DB_NAME="your_database"
   
   # Create backup
   pg_dump -h localhost -U postgres $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
   
   # Keep only last 7 days
   find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
   
   # Upload to S3 (optional)
   aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/database/

Application Backups
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # app_backup.sh
   
   BACKUP_DIR="/var/backups/application"
   DATE=$(date +%Y%m%d_%H%M%S)
   APP_DIR="/var/www/django_graphql_auto"
   
   # Create application backup
   tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
       --exclude='*.pyc' \
       --exclude='__pycache__' \
       --exclude='.git' \
       --exclude='venv' \
       $APP_DIR
   
   # Keep only last 30 days
   find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +30 -delete

Security Considerations
----------------------

SSL/TLS Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Let's Encrypt SSL certificate
   certbot --nginx -d your-domain.com -d www.your-domain.com
   
   # Auto-renewal
   echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

Firewall Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # UFW firewall rules
   ufw default deny incoming
   ufw default allow outgoing
   ufw allow ssh
   ufw allow 'Nginx Full'
   ufw enable

Rate Limiting
~~~~~~~~~~~~

.. code-block:: python

   # Rate limiting middleware
   from django_ratelimit.decorators import ratelimit
   from django.utils.decorators import method_decorator
   
   @method_decorator(ratelimit(key='ip', rate='100/h', method='POST'), name='post')
   class GraphQLView(BaseGraphQLView):
       pass

Troubleshooting Production Issues
--------------------------------

Common Production Problems
~~~~~~~~~~~~~~~~~~~~~~~~~

**High Memory Usage**

.. code-block:: bash

   # Monitor memory usage
   ps aux --sort=-%mem | head -10
   
   # Check for memory leaks
   python -m memory_profiler manage.py runserver

**Database Connection Issues**

.. code-block:: python

   # Check connection pool
   from django.db import connection
   print(f"Queries executed: {len(connection.queries)}")
   
   # Monitor active connections
   SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

**Slow Queries**

.. code-block:: python

   # Enable query logging
   LOGGING = {
       'loggers': {
           'django.db.backends': {
               'level': 'DEBUG',
               'handlers': ['file'],
           },
       },
   }

Emergency Procedures
~~~~~~~~~~~~~~~~~~

**Rollback Deployment**

.. code-block:: bash

   # Quick rollback
   git checkout previous-stable-tag
   sudo systemctl restart django-graphql-auto
   sudo systemctl reload nginx

**Scale Up Resources**

.. code-block:: bash

   # Add more Gunicorn workers
   sudo systemctl edit django-graphql-auto
   # Add: ExecStart=/path/to/gunicorn --workers 8 ...
   sudo systemctl daemon-reload
   sudo systemctl restart django-graphql-auto

Best Practices Summary
---------------------

1. **Security First**: Always disable debug mode and enable HTTPS
2. **Monitor Everything**: Set up comprehensive logging and monitoring
3. **Automate Deployments**: Use CI/CD pipelines for consistent deployments
4. **Test in Staging**: Always test in a production-like environment first
5. **Plan for Scale**: Design for horizontal scaling from the beginning
6. **Backup Regularly**: Implement automated backup and recovery procedures
7. **Document Everything**: Keep deployment procedures well-documented
8. **Monitor Performance**: Track key metrics and set up alerting