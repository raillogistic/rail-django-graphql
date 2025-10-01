Docker Deployment
=================

This guide covers containerizing and deploying Django GraphQL Auto applications using Docker.

.. contents:: Table of Contents
   :local:
   :depth: 2

Docker Fundamentals
------------------

Why Docker for Django GraphQL Auto?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Consistency**: Same environment across development, staging, and production
* **Isolation**: Dependencies and configurations are contained
* **Scalability**: Easy horizontal scaling with container orchestration
* **Portability**: Deploy anywhere Docker runs
* **Reproducibility**: Identical builds every time

Basic Docker Setup
-----------------

Dockerfile
~~~~~~~~~

.. code-block:: dockerfile

   # Dockerfile
   FROM python:3.11-slim
   
   # Set environment variables
   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1
   ENV DJANGO_SETTINGS_MODULE=myproject.settings.production
   
   # Set work directory
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update \
       && apt-get install -y --no-install-recommends \
           postgresql-client \
           build-essential \
           libpq-dev \
           curl \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Python dependencies
   COPY requirements.txt /app/
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy project
   COPY . /app/
   
   # Create non-root user
   RUN adduser --disabled-password --gecos '' appuser \
       && chown -R appuser:appuser /app
   USER appuser
   
   # Collect static files
   RUN python manage.py collectstatic --noinput
   
   # Expose port
   EXPOSE 8000
   
   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:8000/health/ || exit 1
   
   # Run application
   CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]

Multi-stage Dockerfile
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   # Multi-stage Dockerfile for optimized production builds
   
   # Build stage
   FROM python:3.11-slim as builder
   
   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1
   
   WORKDIR /app
   
   # Install build dependencies
   RUN apt-get update && apt-get install -y \
       build-essential \
       libpq-dev \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Python dependencies
   COPY requirements.txt .
   RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt
   
   # Production stage
   FROM python:3.11-slim
   
   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1
   ENV DJANGO_SETTINGS_MODULE=myproject.settings.production
   
   WORKDIR /app
   
   # Install runtime dependencies
   RUN apt-get update && apt-get install -y \
       postgresql-client \
       curl \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy wheels and install
   COPY --from=builder /app/wheels /wheels
   COPY requirements.txt .
   RUN pip install --no-cache /wheels/*
   
   # Create non-root user
   RUN adduser --disabled-password --gecos '' appuser
   
   # Copy project
   COPY --chown=appuser:appuser . /app/
   
   USER appuser
   
   # Collect static files
   RUN python manage.py collectstatic --noinput
   
   EXPOSE 8000
   
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:8000/health/ || exit 1
   
   CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "myproject.wsgi:application"]

Docker Compose
-------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.dev.yml
   version: '3.8'
   
   services:
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: django_graphql_auto_dev
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: postgres
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
   
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
   
     web:
       build:
         context: .
         dockerfile: Dockerfile.dev
       command: python manage.py runserver 0.0.0.0:8000
       volumes:
         - .:/app
       ports:
         - "8000:8000"
       environment:
         - DEBUG=1
         - DB_HOST=db
         - REDIS_URL=redis://redis:6379/1
       depends_on:
         - db
         - redis
   
   volumes:
     postgres_data:

Production Environment
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   
   services:
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: ${DB_NAME}
         POSTGRES_USER: ${DB_USER}
         POSTGRES_PASSWORD: ${DB_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./backups:/backups
       restart: unless-stopped
       networks:
         - backend
   
     redis:
       image: redis:7-alpine
       command: redis-server --appendonly yes
       volumes:
         - redis_data:/data
       restart: unless-stopped
       networks:
         - backend
   
     web:
       build: .
       environment:
         - DJANGO_SETTINGS_MODULE=myproject.settings.production
         - DB_HOST=db
         - REDIS_URL=redis://redis:6379/1
         - SECRET_KEY=${SECRET_KEY}
       volumes:
         - static_volume:/app/staticfiles
         - media_volume:/app/media
       depends_on:
         - db
         - redis
       restart: unless-stopped
       networks:
         - backend
         - frontend
   
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf:ro
         - static_volume:/var/www/static:ro
         - media_volume:/var/www/media:ro
         - ./ssl:/etc/nginx/ssl:ro
       depends_on:
         - web
       restart: unless-stopped
       networks:
         - frontend
   
   volumes:
     postgres_data:
     redis_data:
     static_volume:
     media_volume:
   
   networks:
     frontend:
       driver: bridge
     backend:
       driver: bridge

Environment Configuration
------------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # .env
   # Database
   DB_NAME=django_graphql_auto
   DB_USER=postgres
   DB_PASSWORD=your_secure_password
   DB_HOST=db
   DB_PORT=5432
   
   # Django
   SECRET_KEY=your-super-secret-key-here
   DEBUG=0
   ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
   
   # Cache
   REDIS_URL=redis://redis:6379/1
   
   # GraphQL
   GRAPHQL_MAX_QUERY_COMPLEXITY=1000
   GRAPHQL_MAX_QUERY_DEPTH=10
   GRAPHQL_ENABLE_INTROSPECTION=0

Docker Secrets
~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.secrets.yml
   version: '3.8'
   
   services:
     web:
       secrets:
         - db_password
         - secret_key
       environment:
         - DB_PASSWORD_FILE=/run/secrets/db_password
         - SECRET_KEY_FILE=/run/secrets/secret_key
   
   secrets:
     db_password:
       file: ./secrets/db_password.txt
     secret_key:
       file: ./secrets/secret_key.txt

Nginx Configuration
------------------

Nginx for Docker
~~~~~~~~~~~~~~~

.. code-block:: nginx

   # nginx.conf
   events {
       worker_connections 1024;
   }
   
   http {
       upstream django_app {
           server web:8000;
       }
   
       server {
           listen 80;
           server_name localhost;
   
           # Security headers
           add_header X-Content-Type-Options nosniff;
           add_header X-Frame-Options DENY;
           add_header X-XSS-Protection "1; mode=block";
   
           # Static files
           location /static/ {
               alias /var/www/static/;
               expires 1y;
               add_header Cache-Control "public, immutable";
           }
   
           location /media/ {
               alias /var/www/media/;
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
               
               # CORS headers (if needed)
               add_header Access-Control-Allow-Origin *;
               add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
               add_header Access-Control-Allow-Headers "Content-Type, Authorization";
           }
   
           # Health check
           location /health/ {
               proxy_pass http://django_app;
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
   }

SSL with Let's Encrypt
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.ssl.yml
   version: '3.8'
   
   services:
     certbot:
       image: certbot/certbot
       volumes:
         - ./certbot/conf:/etc/letsencrypt
         - ./certbot/www:/var/www/certbot
       command: certonly --webroot -w /var/www/certbot --force-renewal --email your-email@domain.com -d your-domain.com --agree-tos
   
     nginx:
       volumes:
         - ./certbot/conf:/etc/letsencrypt:ro
         - ./certbot/www:/var/www/certbot:ro

Database Management
------------------

Database Initialization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # init-db.sh
   
   # Wait for database to be ready
   until docker-compose exec db pg_isready -U postgres; do
     echo "Waiting for database..."
     sleep 2
   done
   
   # Run migrations
   docker-compose exec web python manage.py migrate
   
   # Create superuser (if needed)
   docker-compose exec web python manage.py createsuperuser --noinput || true
   
   # Load initial data
   docker-compose exec web python manage.py loaddata initial_data.json

Database Backups
~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # backup-db.sh
   
   BACKUP_DIR="./backups"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   # Create backup directory
   mkdir -p $BACKUP_DIR
   
   # Create database backup
   docker-compose exec -T db pg_dump -U postgres django_graphql_auto | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
   
   # Keep only last 7 backups
   ls -t $BACKUP_DIR/backup_*.sql.gz | tail -n +8 | xargs rm -f
   
   echo "Backup created: backup_$DATE.sql.gz"

Monitoring and Logging
---------------------

Container Monitoring
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.monitoring.yml
   version: '3.8'
   
   services:
     prometheus:
       image: prom/prometheus
       ports:
         - "9090:9090"
       volumes:
         - ./prometheus.yml:/etc/prometheus/prometheus.yml
         - prometheus_data:/prometheus
       command:
         - '--config.file=/etc/prometheus/prometheus.yml'
         - '--storage.tsdb.path=/prometheus'
   
     grafana:
       image: grafana/grafana
       ports:
         - "3000:3000"
       volumes:
         - grafana_data:/var/lib/grafana
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin
   
     cadvisor:
       image: gcr.io/cadvisor/cadvisor
       ports:
         - "8080:8080"
       volumes:
         - /:/rootfs:ro
         - /var/run:/var/run:rw
         - /sys:/sys:ro
         - /var/lib/docker/:/var/lib/docker:ro
   
   volumes:
     prometheus_data:
     grafana_data:

Centralized Logging
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.logging.yml
   version: '3.8'
   
   services:
     elasticsearch:
       image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
       environment:
         - discovery.type=single-node
         - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
       volumes:
         - elasticsearch_data:/usr/share/elasticsearch/data
       ports:
         - "9200:9200"
   
     logstash:
       image: docker.elastic.co/logstash/logstash:8.5.0
       volumes:
         - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
       depends_on:
         - elasticsearch
   
     kibana:
       image: docker.elastic.co/kibana/kibana:8.5.0
       ports:
         - "5601:5601"
       depends_on:
         - elasticsearch
   
     web:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   
   volumes:
     elasticsearch_data:

Scaling and Orchestration
------------------------

Docker Swarm
~~~~~~~~~~~

.. code-block:: yaml

   # docker-stack.yml
   version: '3.8'
   
   services:
     web:
       image: your-registry/django-graphql-auto:latest
       deploy:
         replicas: 3
         update_config:
           parallelism: 1
           delay: 10s
         restart_policy:
           condition: on-failure
         resources:
           limits:
             memory: 512M
           reservations:
             memory: 256M
       networks:
         - backend
         - frontend
   
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       deploy:
         replicas: 2
         placement:
           constraints:
             - node.role == manager
       networks:
         - frontend
   
   networks:
     frontend:
       external: true
     backend:
       external: true

Load Balancing
~~~~~~~~~~~~~

.. code-block:: bash

   # Deploy to swarm
   docker stack deploy -c docker-stack.yml django-app
   
   # Scale services
   docker service scale django-app_web=5
   
   # Update service
   docker service update --image your-registry/django-graphql-auto:v2.0 django-app_web

CI/CD Integration
----------------

GitHub Actions
~~~~~~~~~~~~~

.. code-block:: yaml

   # .github/workflows/docker.yml
   name: Docker Build and Deploy
   
   on:
     push:
       branches: [main]
     pull_request:
       branches: [main]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       services:
         postgres:
           image: postgres:15
           env:
             POSTGRES_PASSWORD: postgres
           options: >-
             --health-cmd pg_isready
             --health-interval 10s
             --health-timeout 5s
             --health-retries 5
   
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
         
         - name: Run tests
           run: |
             python manage.py test
   
     build:
       needs: test
       runs-on: ubuntu-latest
       
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Docker Buildx
           uses: docker/setup-buildx-action@v2
         
         - name: Login to DockerHub
           uses: docker/login-action@v2
           with:
             username: ${{ secrets.DOCKERHUB_USERNAME }}
             password: ${{ secrets.DOCKERHUB_TOKEN }}
         
         - name: Build and push
           uses: docker/build-push-action@v4
           with:
             context: .
             push: true
             tags: |
               your-username/django-graphql-auto:latest
               your-username/django-graphql-auto:${{ github.sha }}
   
     deploy:
       needs: build
       runs-on: ubuntu-latest
       if: github.ref == 'refs/heads/main'
       
       steps:
         - name: Deploy to production
           uses: appleboy/ssh-action@v0.1.5
           with:
             host: ${{ secrets.HOST }}
             username: ${{ secrets.USERNAME }}
             key: ${{ secrets.KEY }}
             script: |
               cd /var/www/django-graphql-auto
               docker-compose pull
               docker-compose up -d
               docker system prune -f

Security Best Practices
-----------------------

Container Security
~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   # Security-focused Dockerfile
   FROM python:3.11-slim
   
   # Use specific versions
   RUN apt-get update && apt-get install -y \
       postgresql-client=15.* \
       && rm -rf /var/lib/apt/lists/*
   
   # Create non-root user with specific UID
   RUN adduser --disabled-password --gecos '' --uid 1001 appuser
   
   # Set secure permissions
   COPY --chown=appuser:appuser . /app/
   RUN chmod -R 755 /app
   
   # Drop privileges
   USER appuser
   
   # Use HTTPS for package installation
   RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org -r requirements.txt

Secrets Management
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Using Docker secrets
   echo "your_secret_key" | docker secret create django_secret_key -
   echo "your_db_password" | docker secret create db_password -

.. code-block:: yaml

   # In docker-compose.yml
   services:
     web:
       secrets:
         - django_secret_key
         - db_password
   
   secrets:
     django_secret_key:
       external: true
     db_password:
       external: true

Network Security
~~~~~~~~~~~~~~

.. code-block:: yaml

   # Network isolation
   networks:
     frontend:
       driver: bridge
       ipam:
         config:
           - subnet: 172.20.0.0/16
     backend:
       driver: bridge
       internal: true
       ipam:
         config:
           - subnet: 172.21.0.0/16

Troubleshooting
--------------

Common Docker Issues
~~~~~~~~~~~~~~~~~~

**Container Won't Start**

.. code-block:: bash

   # Check logs
   docker-compose logs web
   
   # Debug container
   docker-compose run --rm web bash

**Database Connection Issues**

.. code-block:: bash

   # Test database connection
   docker-compose exec web python manage.py dbshell
   
   # Check network connectivity
   docker-compose exec web ping db

**Performance Issues**

.. code-block:: bash

   # Monitor resource usage
   docker stats
   
   # Check container limits
   docker inspect container_name | grep -i memory

**Build Issues**

.. code-block:: bash

   # Clear build cache
   docker system prune -a
   
   # Build with no cache
   docker-compose build --no-cache

Debugging Techniques
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Interactive debugging
   docker-compose run --rm web python manage.py shell
   
   # Attach to running container
   docker-compose exec web bash
   
   # View real-time logs
   docker-compose logs -f web

Best Practices Summary
---------------------

1. **Multi-stage Builds**: Use multi-stage builds to reduce image size
2. **Non-root User**: Always run containers as non-root user
3. **Health Checks**: Implement proper health checks
4. **Resource Limits**: Set appropriate CPU and memory limits
5. **Secrets Management**: Never store secrets in images
6. **Network Isolation**: Use separate networks for different tiers
7. **Regular Updates**: Keep base images and dependencies updated
8. **Monitoring**: Implement comprehensive monitoring and logging
9. **Backup Strategy**: Automate database and volume backups
10. **Security Scanning**: Regularly scan images for vulnerabilities