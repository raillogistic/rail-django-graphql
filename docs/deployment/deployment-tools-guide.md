# 🚀 Deployment Tools Guide - Django GraphQL Auto System

## Overview

This comprehensive guide documents all deployment tools implemented in section **8.4 Deployment Tools** of the Django GraphQL Auto System. These enterprise-grade tools provide automated, secure, and reliable deployment processes with comprehensive monitoring, rollback capabilities, and multi-environment support.

## 📋 Table of Contents

1. [Docker Configuration](#docker-configuration)
2. [CI/CD Pipeline Setup](#cicd-pipeline-setup)
3. [Database Migration Scripts](#database-migration-scripts)
4. [Schema Versioning System](#schema-versioning-system)
5. [Rollback Procedures](#rollback-procedures)
6. [Configuration Examples](#configuration-examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Support Resources](#support-resources)

---

## 🐳 Docker Configuration

### Production Dockerfile

The system includes a multi-stage, security-hardened Dockerfile for production deployments:

```dockerfile
# Dockerfile pour Django GraphQL Auto System
FROM python:3.11-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=rail_django_graphql.settings \
    PORT=8000

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r django && useradd -r -g django django

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer et définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .
COPY requirements-dev.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/media/uploads /app/static /app/logs && \
    chown -R django:django /app

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Changer vers l'utilisateur non-root
USER django

# Exposer le port
EXPOSE $PORT

# Script de santé pour Docker
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health/ || exit 1
```

### Docker Compose Configuration

Complete orchestration with PostgreSQL, Redis, and Nginx:

```yaml
version: "3.8"

services:
  # Base de données PostgreSQL
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: rail_django_graphql
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Cache Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Application Django
  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn rail_django_graphql.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
      - ./static:/app/static
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/rail_django_graphql
      - REDIS_URL=redis://redis:6379/0
      - ALLOWED_HOSTS=localhost,127.0.0.1,web
      - SECRET_KEY=your-secret-key-here
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  postgres_data:
  redis_data:
```

### Usage Examples

**Build and run locally:**

```bash
# Build the Docker image
docker build -t django-graphql-auto .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f web

# Scale the application
docker-compose up -d --scale web=3
```

**Production deployment:**

```bash
# Build for production
docker build -f Dockerfile --target production -t django-graphql-auto:prod .

# Deploy with environment variables
docker run -d \
  --name django-graphql-auto \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://redis:6379/0 \
  -e SECRET_KEY=your-production-secret \
  django-graphql-auto:prod
```

---

## 🔄 CI/CD Pipeline Setup

### GitHub Actions Workflow

Comprehensive CI/CD pipeline with testing, security checks, and deployment:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  release:
    types: [published]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "18"

jobs:
  # Tests et validation du code
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          flake8 rail_django_graphql/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 rail_django_graphql/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Run type checking
        run: |
          mypy rail_django_graphql/

      - name: Run security checks
        run: |
          bandit -r rail_django_graphql/ -f json -o bandit-report.json
          safety check --json --output safety-report.json

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
          DEBUG: True
        run: |
          coverage run -m pytest tests/ -v --tb=short
          coverage xml
          coverage report

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  # Build et déploiement
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.DOCKER_REGISTRY }}/django-graphql-auto:${{ github.sha }} .
          docker build -t ${{ secrets.DOCKER_REGISTRY }}/django-graphql-auto:latest .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ${{ secrets.DOCKER_REGISTRY }}/django-graphql-auto:${{ github.sha }}
          docker push ${{ secrets.DOCKER_REGISTRY }}/django-graphql-auto:latest
```

### Usage Examples

**Setting up GitHub Actions:**

1. **Create workflow file:**

```bash
mkdir -p .github/workflows
cp ci.yml .github/workflows/
```

2. **Configure secrets in GitHub:**

```bash
# Required secrets:
DOCKER_REGISTRY=your-registry.com
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-production-secret-key
```

3. **Trigger deployment:**

```bash
# Push to main branch triggers deployment
git push origin main

# Create release for production deployment
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

---

## 🗄️ Database Migration Scripts

### Automated Deployment Script

The `scripts/deploy.py` provides comprehensive deployment automation:

```python
#!/usr/bin/env python3
"""
Script de déploiement automatisé pour Django GraphQL Auto System
Gère les migrations de base de données, les vérifications de santé et le déploiement sécurisé.
"""

import os
import sys
import subprocess
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class DeploymentManager:
    """Gestionnaire de déploiement avec migrations et vérifications de sécurité."""

    def __init__(self, environment: str = 'production'):
        self.environment = environment
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        self.deployment_config = self._load_deployment_config()

    def deploy(self) -> bool:
        """Exécute le processus de déploiement complet."""
        try:
            logger.info(f"Début du déploiement pour l'environnement: {self.environment}")

            # 1. Vérifications pré-déploiement
            self.pre_deployment_checks()

            # 2. Sauvegarde de la base de données
            backup_file = self.create_database_backup()

            # 3. Mode maintenance
            if self.deployment_config.get('maintenance_mode', True):
                self.enable_maintenance_mode()

            # 4. Migrations de base de données
            self.run_database_migrations()

            # 5. Collecte des fichiers statiques
            if self.deployment_config.get('static_files', True):
                self.collect_static_files()

            # 6. Redémarrage des services
            self.restart_services()

            # 7. Vérifications post-déploiement
            self.post_deployment_checks()

            # 8. Désactivation du mode maintenance
            if self.deployment_config.get('maintenance_mode', True):
                self.disable_maintenance_mode()

            logger.info("Déploiement terminé avec succès!")
            return True

        except Exception as e:
            logger.error(f"Erreur lors du déploiement: {e}")

            # Rollback en cas d'erreur
            if self.deployment_config.get('rollback_on_failure', True):
                self.rollback_deployment(backup_file)

            return False
```

### Usage Examples

**Basic deployment:**

```bash
# Deploy to production
python scripts/deploy.py --environment production

# Deploy to staging
python scripts/deploy.py --environment staging

# Deploy with custom configuration
python scripts/deploy.py --config deployment-custom.json
```

**Advanced deployment options:**

```bash
# Deploy without database backup
python scripts/deploy.py --no-backup

# Deploy with specific migration target
python scripts/deploy.py --migrate-to 0001_initial

# Deploy with rollback disabled
python scripts/deploy.py --no-rollback

# Dry run (simulation)
python scripts/deploy.py --dry-run
```

**Configuration file example (`deployment-production.json`):**

```json
{
  "database_backup": true,
  "run_tests": true,
  "health_check_timeout": 300,
  "rollback_on_failure": true,
  "maintenance_mode": true,
  "static_files": true,
  "cache_clear": true,
  "services": ["web", "worker", "scheduler"],
  "health_checks": ["database", "redis", "graphql_endpoint"]
}
```

---

## 📋 Schema Versioning System

### Schema Version Management

The system includes comprehensive GraphQL schema versioning with the `core/schema_versioning.py` module:

```python
from rail_django_graphql.core.schema_versioning import SchemaVersionManager

# Initialize the schema version manager
manager = SchemaVersionManager()

# Create a new schema version
version = manager.create_version(
    version="1.2.0",
    description="Added user authentication and file upload mutations",
    schema_content=current_schema_content
)

# Activate a specific version
manager.activate_version("1.2.0")

# List all versions
versions = manager.list_versions()

# Compare versions
diff = manager.compare_versions("1.1.0", "1.2.0")
```

### Management Commands

Use Django management commands for schema versioning:

```bash
# Create a new schema version
python manage.py manage_schema_versions create \
  --version 1.2.0 \
  --description "Added user authentication features"

# Activate a specific version
python manage.py manage_schema_versions activate --version 1.2.0

# List all schema versions
python manage.py manage_schema_versions list

# Show version details
python manage.py manage_schema_versions show --version 1.2.0

# Compare two versions
python manage.py manage_schema_versions compare --from 1.1.0 --to 1.2.0

# Delete a version
python manage.py manage_schema_versions delete --version 1.0.0

# Rollback to previous version
python manage.py manage_schema_versions rollback

# View version history
python manage.py manage_schema_versions history
```

### Usage Examples

**Automated schema versioning in CI/CD:**

```yaml
# In your GitHub Actions workflow
- name: Create schema version
  run: |
    python manage.py manage_schema_versions create \
      --version ${{ github.ref_name }} \
      --description "Release ${{ github.ref_name }}"

- name: Activate new schema version
  run: |
    python manage.py manage_schema_versions activate \
      --version ${{ github.ref_name }}
```

**Schema migration script:**

```bash
#!/bin/bash
# schema_migration.sh

# Get current version
CURRENT_VERSION=$(python manage.py manage_schema_versions list --active-only --format json | jq -r '.version')

# Create backup
python manage.py manage_schema_versions create \
  --version "backup-$(date +%Y%m%d-%H%M%S)" \
  --description "Backup before migration"

# Apply new schema
python manage.py manage_schema_versions activate --version $1

# Verify deployment
if ! python scripts/health_check.py --check graphql; then
  echo "Health check failed, rolling back..."
  python manage.py manage_schema_versions rollback
  exit 1
fi

echo "Schema migration completed successfully"
```

---

## 🔄 Rollback Procedures

### Automated Rollback System

The `scripts/rollback.py` provides comprehensive rollback capabilities:

```python
#!/usr/bin/env python3
"""
Système de rollback complet pour Django GraphQL Auto System
Gère les rollbacks de base de données, fichiers statiques, et schémas GraphQL
"""

class RollbackManager:
    """Gestionnaire de rollback avec vérifications de sécurité."""

    def __init__(self, config_file: str = 'rollback_config.json'):
        self.config = self._load_config(config_file)
        self.backup_dir = Path(self.config['backup_directory'])

    def rollback_to_backup(self, backup_name: str) -> bool:
        """Effectue un rollback complet vers une sauvegarde spécifique."""
        try:
            logger.info(f"Début du rollback vers: {backup_name}")

            # 1. Vérifications de sécurité
            if not self._verify_backup_integrity(backup_name):
                raise RollbackError("Intégrité de la sauvegarde compromise")

            # 2. Arrêt des services
            self._stop_services()

            # 3. Sauvegarde pré-rollback
            if self.config['safety_checks']['pre_rollback_backup']:
                self._create_pre_rollback_backup()

            # 4. Restauration de la base de données
            self._restore_database(backup_name)

            # 5. Restauration des fichiers statiques
            self._restore_static_files(backup_name)

            # 6. Restauration des fichiers média
            self._restore_media_files(backup_name)

            # 7. Restauration du schéma GraphQL
            self._restore_schema_version(backup_name)

            # 8. Redémarrage des services
            self._start_services()

            # 9. Vérification post-rollback
            self._verify_rollback_success()

            logger.info("Rollback terminé avec succès!")
            return True

        except Exception as e:
            logger.error(f"Erreur lors du rollback: {e}")
            self._send_rollback_notification(False, str(e))
            return False
```

### Usage Examples

**List available backups:**

```bash
# List all available backups
python scripts/rollback.py list

# List backups with details
python scripts/rollback.py list --detailed

# List recent backups only
python scripts/rollback.py list --recent 7
```

**Perform rollback:**

```bash
# Rollback to specific backup
python scripts/rollback.py rollback backup_20240115_143022

# Rollback to previous version
python scripts/rollback.py rollback --previous

# Rollback with confirmation prompt
python scripts/rollback.py rollback backup_20240115_143022 --confirm

# Emergency rollback (skip safety checks)
python scripts/rollback.py rollback backup_20240115_143022 --emergency
```

**Verify rollback:**

```bash
# Verify rollback success
python scripts/rollback.py verify

# Verify specific backup integrity
python scripts/rollback.py verify backup_20240115_143022

# Health check after rollback
python scripts/health_check.py --comprehensive
```

### Rollback Configuration

**Configuration file (`rollback_config.json`):**

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "rail_django_graphql",
    "user": "postgres",
    "password": "postgres"
  },
  "backup_directory": "/app/backups",
  "max_rollback_age_days": 30,
  "safety_checks": {
    "require_confirmation": true,
    "check_active_connections": true,
    "verify_backup_integrity": true,
    "test_rollback": false,
    "pre_rollback_backup": true
  },
  "notifications": {
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/services/...",
      "channel": "#deployments"
    },
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "from_email": "deployments@yourcompany.com",
      "to_emails": ["admin@yourcompany.com"]
    }
  },
  "docker_compose": {
    "file": "docker-compose.yml",
    "services": ["web", "worker", "scheduler"]
  },
  "rollback_procedures": {
    "pre_rollback_backup": true,
    "service_stop_timeout": 30,
    "service_start_timeout": 60,
    "health_check_retries": 5,
    "health_check_interval": 10
  },
  "monitoring": {
    "log_file": "/app/logs/rollback.log",
    "metrics_enabled": true,
    "alert_on_failure": true
  }
}
```

---

## 🏥 Health Check System

### Comprehensive Health Monitoring

The `scripts/health_check.py` provides extensive health monitoring:

```python
#!/usr/bin/env python3
"""
Système de vérification de santé complet pour Django GraphQL Auto
Conçu pour la sécurité de déploiement et la surveillance
"""

class HealthChecker:
    """Vérificateur de santé avec surveillance complète."""

    def __init__(self, config_file: str = 'health_check_config.json'):
        self.config = self._load_config(config_file)
        self.results = []

    def run_all_checks(self) -> Dict[str, Any]:
        """Exécute toutes les vérifications de santé."""
        checks = [
            ('database', self.check_database),
            ('redis', self.check_redis),
            ('application', self.check_application),
            ('graphql', self.check_graphql_endpoint),
            ('filesystem', self.check_filesystem),
            ('performance', self.check_performance)
        ]

        results = {}
        for name, check_func in checks:
            try:
                result = check_func()
                results[name] = result
                self.results.append(result)
            except Exception as e:
                error_result = HealthCheckResult(
                    name=name,
                    status='critical',
                    message=f"Health check failed: {str(e)}",
                    duration=0
                )
                results[name] = error_result
                self.results.append(error_result)

        return results
```

### Usage Examples

**Basic health checks:**

```bash
# Run all health checks
python scripts/health_check.py

# Run specific health check
python scripts/health_check.py --check database

# Run with JSON output
python scripts/health_check.py --format json

# Run with detailed output
python scripts/health_check.py --verbose
```

**Advanced health monitoring:**

```bash
# Continuous monitoring
python scripts/health_check.py --monitor --interval 30

# Health check with alerts
python scripts/health_check.py --alert-on-failure

# Export health metrics
python scripts/health_check.py --export-metrics health_metrics.json

# Integration with monitoring systems
python scripts/health_check.py --prometheus-endpoint http://localhost:9090
```

---

## ⚙️ Configuration Examples

### Environment-Specific Configurations

**Production Environment (`.env.production`):**

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-production-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/production_db

# Redis
REDIS_URL=redis://redis-host:6379/0

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# GraphQL
GRAPHQL_QUERY_DEPTH_LIMIT=10
GRAPHQL_QUERY_COMPLEXITY_LIMIT=1000
GRAPHQL_RATE_LIMIT_PER_MINUTE=100

# File Uploads
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=jpg,jpeg,png,pdf,doc,docx

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_PERFORMANCE_MONITORING=True
```

**Staging Environment (`.env.staging`):**

```bash
# Django Settings
DEBUG=True
SECRET_KEY=staging-secret-key
ALLOWED_HOSTS=staging.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@staging-db:5432/staging_db

# Redis
REDIS_URL=redis://staging-redis:6379/0

# GraphQL
GRAPHQL_QUERY_DEPTH_LIMIT=15
GRAPHQL_QUERY_COMPLEXITY_LIMIT=2000
GRAPHQL_RATE_LIMIT_PER_MINUTE=200

# Testing
ENABLE_GRAPHQL_PLAYGROUND=True
ENABLE_DEBUG_TOOLBAR=True
```

---

## 🎯 Best Practices

### 1. Security Best Practices

- **Use non-root users in Docker containers**
- **Implement proper secret management**
- **Enable HTTPS in production**
- **Regular security updates**
- **Input validation and sanitization**

### 2. Performance Optimization

- **Use multi-stage Docker builds**
- **Implement proper caching strategies**
- **Optimize database queries**
- **Use CDN for static files**
- **Monitor performance metrics**

### 3. Deployment Safety

- **Always create backups before deployment**
- **Use blue-green deployment strategies**
- **Implement comprehensive health checks**
- **Have rollback procedures ready**
- **Test deployments in staging first**

### 4. Monitoring and Alerting

- **Set up comprehensive logging**
- **Implement health check endpoints**
- **Use monitoring tools (Prometheus, Grafana)**
- **Configure alerting for critical issues**
- **Regular performance reviews**

### 5. Documentation and Maintenance

- **Keep deployment documentation updated**
- **Document configuration changes**
- **Regular backup testing**
- **Security audit schedules**
- **Team training on deployment procedures**

---

## 🚨 Troubleshooting

### Common Issues and Solutions

**1. Database Migration Failures:**

```bash
# Check migration status
python manage.py showmigrations

# Apply specific migration
python manage.py migrate app_name 0001 --fake

# Reset migrations (development only)
python manage.py migrate app_name zero
```

**2. Docker Build Issues:**

```bash
# Clear Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -t django-graphql-auto .

# Check Docker logs
docker logs container_name
```

**3. Health Check Failures:**

```bash
# Detailed health check
python scripts/health_check.py --verbose

# Check specific component
python scripts/health_check.py --check database --debug

# View health check logs
tail -f /app/logs/health_check.log
```

**4. Schema Version Issues:**

```bash
# Check schema version status
python manage.py manage_schema_versions list

# Validate schema integrity
python manage.py manage_schema_versions validate

# Force schema refresh
python manage.py manage_schema_versions refresh
```

---

## 📞 Support and Resources

- **Documentation**: `/docs/deployment/`
- **Health Monitoring**: `/health/`
- **GraphQL Playground**: `/graphql/` (development only)
- **Admin Interface**: `/admin/`
- **Logs Location**: `/app/logs/`
- **Backup Location**: `/app/backups/`

For additional support, refer to the project documentation or contact the development team.
