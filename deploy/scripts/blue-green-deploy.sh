#!/bin/bash

# Blue-Green Deployment Script for Django GraphQL Auto System
# This script performs zero-downtime deployments using Docker Compose

set -euo pipefail

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
HEALTH_CHECK_URL="http://localhost/health/"
HEALTH_CHECK_TIMEOUT=300
HEALTH_CHECK_INTERVAL=10
BACKUP_RETENTION_DAYS=7

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required environment variables are set
check_environment() {
    log_info "Checking environment variables..."
    
    required_vars=(
        "IMAGE_TAG"
        "DATABASE_URL"
        "SECRET_KEY"
        "REDIS_URL"
        "ENVIRONMENT"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_success "All required environment variables are set"
}

# Create backup of current deployment
create_backup() {
    log_info "Creating backup of current deployment..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -q; then
        log_info "Creating database backup..."
        docker-compose -f "$COMPOSE_FILE" exec -T db \
            pg_dump -U postgres django_graphql > "$backup_dir/database.sql"
        log_success "Database backup created: $backup_dir/database.sql"
    else
        log_warning "Database not available for backup"
    fi
    
    # Backup current docker-compose configuration
    if [[ -f "$COMPOSE_FILE" ]]; then
        cp "$COMPOSE_FILE" "$backup_dir/"
        log_success "Configuration backup created: $backup_dir/$COMPOSE_FILE"
    fi
    
    # Store current image tags
    docker-compose -f "$COMPOSE_FILE" config | grep "image:" > "$backup_dir/current_images.txt" || true
    
    log_success "Backup created in $backup_dir"
    echo "$backup_dir" > .last_backup
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $BACKUP_RETENTION_DAYS days)..."
    
    if [[ -d "backups" ]]; then
        find backups -type d -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
        log_success "Old backups cleaned up"
    fi
}

# Pull new images
pull_images() {
    log_info "Pulling new Docker images..."
    
    # Set the new image tag
    export IMAGE_TAG="${IMAGE_TAG}"
    
    if docker-compose -f "$COMPOSE_FILE" pull; then
        log_success "Images pulled successfully"
    else
        log_error "Failed to pull images"
        exit 1
    fi
}

# Health check function
health_check() {
    local url="$1"
    local timeout="$2"
    local interval="$3"
    
    log_info "Performing health check on $url..."
    
    local elapsed=0
    while [[ $elapsed -lt $timeout ]]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check failed, retrying in ${interval}s... (${elapsed}/${timeout}s elapsed)"
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    
    log_error "Health check failed after ${timeout}s"
    return 1
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    if docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py migrate --noinput; then
        log_success "Database migrations completed"
    else
        log_error "Database migrations failed"
        return 1
    fi
}

# Collect static files
collect_static() {
    log_info "Collecting static files..."
    
    if docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py collectstatic --noinput; then
        log_success "Static files collected"
    else
        log_error "Static file collection failed"
        return 1
    fi
}

# Deploy new version
deploy_new_version() {
    log_info "Deploying new version..."
    
    # Start new containers
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        log_success "New containers started"
    else
        log_error "Failed to start new containers"
        return 1
    fi
    
    # Wait for containers to be ready
    log_info "Waiting for containers to be ready..."
    sleep 30
    
    # Perform health check
    if health_check "$HEALTH_CHECK_URL" "$HEALTH_CHECK_TIMEOUT" "$HEALTH_CHECK_INTERVAL"; then
        log_success "New version is healthy"
        return 0
    else
        log_error "New version failed health check"
        return 1
    fi
}

# Rollback to previous version
rollback() {
    log_error "Rolling back to previous version..."
    
    if [[ -f ".last_backup" ]]; then
        local backup_dir=$(cat .last_backup)
        
        if [[ -d "$backup_dir" && -f "$backup_dir/$COMPOSE_FILE" ]]; then
            # Restore previous configuration
            cp "$backup_dir/$COMPOSE_FILE" .
            
            # Restart with previous configuration
            docker-compose -f "$COMPOSE_FILE" up -d
            
            # Health check
            if health_check "$HEALTH_CHECK_URL" "$HEALTH_CHECK_TIMEOUT" "$HEALTH_CHECK_INTERVAL"; then
                log_success "Rollback completed successfully"
                return 0
            else
                log_error "Rollback failed health check"
                return 1
            fi
        else
            log_error "Backup not found, cannot rollback"
            return 1
        fi
    else
        log_error "No backup information found"
        return 1
    fi
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local emoji="✅"
        if [[ "$status" == "error" ]]; then
            emoji="❌"
        elif [[ "$status" == "warning" ]]; then
            emoji="⚠️"
        fi
        
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"$emoji $message\"}" \
            2>/dev/null || true
    fi
}

# Main deployment function
main() {
    log_info "Starting blue-green deployment..."
    log_info "Image tag: $IMAGE_TAG"
    log_info "Environment: $ENVIRONMENT"
    
    # Trap to handle errors
    trap 'log_error "Deployment failed"; send_notification "error" "Deployment failed for $IMAGE_TAG"; exit 1' ERR
    
    # Pre-deployment checks
    check_environment
    
    # Create backup
    create_backup
    
    # Clean old backups
    cleanup_old_backups
    
    # Pull new images
    pull_images
    
    # Run migrations
    if ! run_migrations; then
        log_error "Migration failed, aborting deployment"
        exit 1
    fi
    
    # Collect static files
    if ! collect_static; then
        log_error "Static file collection failed, aborting deployment"
        exit 1
    fi
    
    # Deploy new version
    if deploy_new_version; then
        log_success "Deployment completed successfully!"
        send_notification "success" "Deployment successful for $IMAGE_TAG"
        
        # Clean up old Docker images
        log_info "Cleaning up old Docker images..."
        docker image prune -f || true
        
        log_success "Blue-green deployment completed!"
    else
        log_error "Deployment failed, initiating rollback..."
        if rollback; then
            log_warning "Rollback completed"
            send_notification "warning" "Deployment failed for $IMAGE_TAG, rollback completed"
        else
            log_error "Rollback failed!"
            send_notification "error" "Deployment and rollback failed for $IMAGE_TAG"
        fi
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi