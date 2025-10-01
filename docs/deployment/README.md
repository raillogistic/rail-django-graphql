# Django GraphQL Auto System - Deployment Guide

This comprehensive guide covers the deployment of the Django GraphQL Auto System in production and development environments.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Development Deployment](#development-deployment)
5. [Production Deployment](#production-deployment)
6. [Monitoring and Health Checks](#monitoring-and-health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

## Overview

The Django GraphQL Auto System uses a containerized architecture with the following components:

- **Django Application**: GraphQL API server
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage
- **Nginx**: Reverse proxy and static file serving
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards
- **Alertmanager**: Alert routing and notifications

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or CentOS 8+
- **CPU**: Minimum 2 cores (4+ recommended for production)
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Storage**: Minimum 20GB free space (100GB+ recommended for production)
- **Network**: Internet access for package downloads

### Required Software

- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for production)

### Domain and SSL Setup

For production deployment, you'll need:
- A registered domain name
- SSL certificates (Let's Encrypt recommended)
- DNS configuration pointing to your server

## Environment Setup

### 1. Server Preparation

Run the automated setup script:

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/your-repo/django-graphql/main/deploy/scripts/setup-environment.sh | bash

# Or manually:
git clone https://github.com/your-repo/django-graphql.git
cd django-graphql
chmod +x deploy/scripts/setup-environment.sh
sudo ./deploy/scripts/setup-environment.sh
```

This script will:
- Install Docker and Docker Compose
- Create application user and directories
- Set up Nginx
- Configure SSL certificates
- Install monitoring tools
- Set up log rotation

### 2. Environment Variables

Create environment files for your deployment:

```bash
# Production environment
cp .env.example .env.production

# Development environment
cp .env.example .env.development
```

Edit the environment files with your specific configuration:

```bash
# .env.production
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=django_graphql_prod
DB_USER=django_user
DB_PASSWORD=secure-database-password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure-redis-password

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Monitoring
PROMETHEUS_RETENTION_TIME=30d
GRAFANA_ADMIN_PASSWORD=secure-grafana-password

# SSL
SSL_DOMAIN=yourdomain.com
SSL_EMAIL=admin@yourdomain.com
```

## Development Deployment

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/django-graphql.git
   cd django-graphql
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env.development
   # Edit .env.development with your settings
   ```

3. **Start development environment**:
   ```bash
   docker-compose -f deploy/docker/docker-compose.development.yml up -d
   ```

4. **Run initial setup**:
   ```bash
   # Run migrations
   docker-compose -f deploy/docker/docker-compose.development.yml exec web python manage.py migrate
   
   # Create superuser
   docker-compose -f deploy/docker/docker-compose.development.yml exec web python manage.py createsuperuser
   
   # Collect static files
   docker-compose -f deploy/docker/docker-compose.development.yml exec web python manage.py collectstatic --noinput
   ```

### Development Services

The development environment includes:

- **Django App**: http://localhost:8000
- **pgAdmin**: http://localhost:5050 (admin@admin.com / admin)
- **Redis Commander**: http://localhost:8081
- **MailHog**: http://localhost:8025
- **Jupyter Notebook**: http://localhost:8888

### Development Commands

```bash
# View logs
docker-compose -f deploy/docker/docker-compose.development.yml logs -f

# Run tests
docker-compose -f deploy/docker/docker-compose.development.yml exec web python manage.py test

# Access Django shell
docker-compose -f deploy/docker/docker-compose.development.yml exec web python manage.py shell

# Stop services
docker-compose -f deploy/docker/docker-compose.development.yml down
```

## Production Deployment

### Method 1: Automated Deployment (Recommended)

1. **Prepare the server**:
   ```bash
   # Run setup script
   sudo ./deploy/scripts/setup-environment.sh
   ```

2. **Configure environment**:
   ```bash
   # Copy and edit production environment
   cp .env.example .env.production
   # Edit with your production settings
   ```

3. **Deploy using the deployment script**:
   ```bash
   # Initial deployment
   ./deploy/scripts/blue-green-deploy.sh deploy

   # Or use GitHub Actions for automated deployment
   git push origin main  # Triggers deployment pipeline
   ```

### Method 2: Manual Deployment

1. **Build and start services**:
   ```bash
   # Build production images
   docker-compose -f deploy/docker/docker-compose.production.yml build

   # Start services
   docker-compose -f deploy/docker/docker-compose.production.yml up -d
   ```

2. **Run initial setup**:
   ```bash
   # Run migrations
   docker-compose -f deploy/docker/docker-compose.production.yml exec web python manage.py migrate

   # Create superuser
   docker-compose -f deploy/docker/docker-compose.production.yml exec web python manage.py createsuperuser

   # Collect static files
   docker-compose -f deploy/docker/docker-compose.production.yml exec web python manage.py collectstatic --noinput
   ```

3. **Configure Nginx**:
   ```bash
   # Copy Nginx configuration
   sudo cp deploy/nginx/default /etc/nginx/sites-available/django-graphql
   sudo ln -s /etc/nginx/sites-available/django-graphql /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Production Services

The production environment includes:

- **Django App**: https://yourdomain.com
- **Admin Interface**: https://yourdomain.com/admin/
- **GraphQL Endpoint**: https://yourdomain.com/graphql/
- **Prometheus**: http://yourdomain.com:9090
- **Grafana**: http://yourdomain.com:3000
- **Health Check**: https://yourdomain.com/health/

### SSL Certificate Setup

#### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

#### Using Custom Certificates

```bash
# Copy your certificates
sudo cp your-certificate.crt /etc/ssl/certs/
sudo cp your-private-key.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-private-key.key

# Update Nginx configuration with certificate paths
```

## Monitoring and Health Checks

### Health Check Endpoints

The application provides several health check endpoints:

- **Application Health**: `/health/`
- **Database Health**: `/health/db/`
- **Cache Health**: `/health/cache/`
- **Detailed Health**: `/health/detailed/`

### Manual Health Check

Run the comprehensive health check script:

```bash
# Check all components
python deploy/monitoring/health-check.py

# Check specific component
python deploy/monitoring/health-check.py --component django

# JSON output for monitoring systems
python deploy/monitoring/health-check.py --format json

# Prometheus metrics format
python deploy/monitoring/health-check.py --format prometheus
```

### Monitoring Dashboard

Access Grafana at `http://yourdomain.com:3000`:

- **Username**: admin
- **Password**: (set in environment variables)

Pre-configured dashboards:
- Django Application Metrics
- Database Performance
- System Resources
- Error Tracking

### Alerting

Alerts are configured in Prometheus and routed through Alertmanager:

- **Critical Alerts**: Immediate notification via email/Slack
- **Warning Alerts**: Periodic notifications
- **Info Alerts**: Dashboard notifications only

Configure alert destinations in `deploy/monitoring/alertmanager.yml`.

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check container logs
docker-compose logs [service-name]

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart [service-name]
```

#### 2. Database Connection Issues

```bash
# Check database container
docker-compose logs postgres

# Test database connection
docker-compose exec web python manage.py dbshell

# Check database settings
docker-compose exec web python manage.py check --database default
```

#### 3. Static Files Not Loading

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t

# Check file permissions
ls -la /var/www/static/
```

#### 4. SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in /etc/ssl/certs/your-cert.crt -text -noout | grep "Not After"

# Test SSL configuration
openssl s_client -connect yourdomain.com:443

# Renew Let's Encrypt certificate
sudo certbot renew
```

### Log Locations

- **Application Logs**: `docker-compose logs web`
- **Nginx Logs**: `/var/log/nginx/`
- **System Logs**: `/var/log/syslog`
- **Docker Logs**: `/var/lib/docker/containers/`

### Performance Tuning

#### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('django_graphql_prod'));
```

#### Application Optimization

```bash
# Check memory usage
docker stats

# Profile application
docker-compose exec web python manage.py runprofileserver

# Check for memory leaks
docker-compose exec web python -m memory_profiler your_script.py
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor system health via Grafana
- Check error logs
- Verify backup completion

#### Weekly
- Review performance metrics
- Update security patches
- Clean up old logs

#### Monthly
- Update dependencies
- Review and rotate secrets
- Capacity planning review

### Backup and Recovery

#### Database Backup

```bash
# Manual backup
docker-compose exec postgres pg_dump -U django_user django_graphql_prod > backup_$(date +%Y%m%d).sql

# Automated backup (add to crontab)
0 2 * * * /path/to/backup-script.sh
```

#### Application Backup

```bash
# Backup application data
tar -czf app_backup_$(date +%Y%m%d).tar.gz /opt/django-graphql/

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz /etc/nginx/ /etc/ssl/
```

#### Recovery Process

```bash
# Restore database
docker-compose exec postgres psql -U django_user -d django_graphql_prod < backup_20231201.sql

# Restore application
tar -xzf app_backup_20231201.tar.gz -C /

# Restart services
docker-compose restart
```

### Updates and Upgrades

#### Application Updates

```bash
# Pull latest code
git pull origin main

# Build new images
docker-compose build

# Deploy with zero downtime
./deploy/scripts/blue-green-deploy.sh deploy
```

#### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker
sudo apt install docker-ce docker-ce-cli containerd.io

# Update Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

### Scaling

#### Horizontal Scaling

```bash
# Scale web containers
docker-compose up -d --scale web=3

# Use load balancer (Nginx configuration)
upstream django_app {
    server web1:8000;
    server web2:8000;
    server web3:8000;
}
```

#### Vertical Scaling

Update resource limits in `docker-compose.production.yml`:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Security Considerations

### Security Checklist

- [ ] Use strong, unique passwords
- [ ] Enable SSL/TLS encryption
- [ ] Keep software updated
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Regular security scans
- [ ] Backup encryption
- [ ] Access control reviews

### Security Monitoring

```bash
# Check for security updates
sudo apt list --upgradable | grep -i security

# Scan for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image your-image

# Monitor failed login attempts
sudo grep "Failed password" /var/log/auth.log
```

## Support and Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [GraphQL Documentation](https://graphql.org/learn/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)

### Community
- [Django Community](https://www.djangoproject.com/community/)
- [GraphQL Community](https://graphql.org/community/)
- [Docker Community](https://www.docker.com/community)

### Getting Help

1. Check the troubleshooting section
2. Review application logs
3. Search existing issues on GitHub
4. Create a new issue with detailed information
5. Contact the development team

---

For additional help or questions, please refer to the project repository or contact the development team.