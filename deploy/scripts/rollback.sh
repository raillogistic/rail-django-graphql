#!/bin/bash

# Rollback Script for Django GraphQL Auto System
# This script provides quick rollback functionality for failed deployments

set -euo pipefail

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
HEALTH_CHECK_URL="http://localhost/health/"
HEALTH_CHECK_TIMEOUT=180
HEALTH_CHECK_INTERVAL=10

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

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Rollback Django GraphQL Auto System to previous version

OPTIONS:
    -b, --backup-dir DIR    Specify backup directory to rollback to
    -l, --list-backups      List available backups
    -f, --force             Force rollback without confirmation
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Rollback to last backup
    $0 -b backups/20231201_143022  # Rollback to specific backup
    $0 -l                   # List available backups
    $0 -f                   # Force rollback without confirmation

EOF
}

# List available backups
list_backups() {
    log_info "Available backups:"
    
    if [[ -d "backups" ]]; then
        local backups=($(find backups -maxdepth 1 -type d -name "*_*" | sort -r))
        
        if [[ ${#backups[@]} -eq 0 ]]; then
            log_warning "No backups found"
            return 1
        fi
        
        for backup in "${backups[@]}"; do
            local backup_name=$(basename "$backup")
            local backup_date=$(echo "$backup_name" | sed 's/_/ /' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3/')
            
            echo "  - $backup_name ($backup_date)"
            
            # Show what's in the backup
            if [[ -f "$backup/current_images.txt" ]]; then
                echo "    Images: $(cat "$backup/current_images.txt" | grep -o 'image:.*' | head -1 | cut -d':' -f2- || echo 'Unknown')"
            fi
            
            if [[ -f "$backup/database.sql" ]]; then
                local db_size=$(du -h "$backup/database.sql" | cut -f1)
                echo "    Database backup: $db_size"
            fi
        done
    else
        log_warning "No backups directory found"
        return 1
    fi
}

# Get the backup directory to use
get_backup_dir() {
    local specified_backup="$1"
    
    if [[ -n "$specified_backup" ]]; then
        if [[ -d "$specified_backup" ]]; then
            echo "$specified_backup"
            return 0
        else
            log_error "Specified backup directory does not exist: $specified_backup"
            return 1
        fi
    fi
    
    # Use last backup
    if [[ -f ".last_backup" ]]; then
        local last_backup=$(cat .last_backup)
        if [[ -d "$last_backup" ]]; then
            echo "$last_backup"
            return 0
        else
            log_warning "Last backup directory not found: $last_backup"
        fi
    fi
    
    # Find most recent backup
    if [[ -d "backups" ]]; then
        local recent_backup=$(find backups -maxdepth 1 -type d -name "*_*" | sort -r | head -1)
        if [[ -n "$recent_backup" ]]; then
            echo "$recent_backup"
            return 0
        fi
    fi
    
    log_error "No backup found to rollback to"
    return 1
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

# Confirm rollback action
confirm_rollback() {
    local backup_dir="$1"
    local force="$2"
    
    if [[ "$force" == "true" ]]; then
        return 0
    fi
    
    log_warning "This will rollback the application to backup: $(basename "$backup_dir")"
    log_warning "Current running containers will be stopped and replaced"
    
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
}

# Stop current containers
stop_current_containers() {
    log_info "Stopping current containers..."
    
    if docker-compose -f "$COMPOSE_FILE" down; then
        log_success "Current containers stopped"
    else
        log_warning "Failed to stop some containers"
    fi
}

# Restore configuration
restore_configuration() {
    local backup_dir="$1"
    
    log_info "Restoring configuration from backup..."
    
    if [[ -f "$backup_dir/$COMPOSE_FILE" ]]; then
        cp "$backup_dir/$COMPOSE_FILE" .
        log_success "Configuration restored"
    else
        log_error "Configuration file not found in backup"
        return 1
    fi
    
    # Restore environment file if it exists
    if [[ -f "$backup_dir/.env" ]]; then
        cp "$backup_dir/.env" .
        log_success "Environment file restored"
    fi
}

# Restore database
restore_database() {
    local backup_dir="$1"
    local restore_db="$2"
    
    if [[ "$restore_db" != "true" ]]; then
        log_info "Skipping database restore"
        return 0
    fi
    
    if [[ ! -f "$backup_dir/database.sql" ]]; then
        log_warning "No database backup found, skipping database restore"
        return 0
    fi
    
    log_info "Restoring database from backup..."
    
    # Start database container
    docker-compose -f "$COMPOSE_FILE" up -d db
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Check if database is ready
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -q; then
            break
        fi
        log_info "Waiting for database... ($retries retries left)"
        sleep 2
        retries=$((retries - 1))
    done
    
    if [[ $retries -eq 0 ]]; then
        log_error "Database not ready for restore"
        return 1
    fi
    
    # Drop and recreate database
    docker-compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS django_graphql;"
    docker-compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -c "CREATE DATABASE django_graphql;"
    
    # Restore database
    if docker-compose -f "$COMPOSE_FILE" exec -T db psql -U postgres django_graphql < "$backup_dir/database.sql"; then
        log_success "Database restored successfully"
    else
        log_error "Database restore failed"
        return 1
    fi
}

# Start containers with restored configuration
start_containers() {
    log_info "Starting containers with restored configuration..."
    
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        log_success "Containers started"
    else
        log_error "Failed to start containers"
        return 1
    fi
    
    # Wait for containers to be ready
    log_info "Waiting for containers to be ready..."
    sleep 30
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

# Main rollback function
perform_rollback() {
    local backup_dir="$1"
    local force="$2"
    local restore_db="$3"
    
    log_info "Starting rollback process..."
    log_info "Backup directory: $backup_dir"
    
    # Confirm rollback
    confirm_rollback "$backup_dir" "$force"
    
    # Create a backup of current state before rollback
    log_info "Creating backup of current state before rollback..."
    local pre_rollback_backup="backups/pre_rollback_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$pre_rollback_backup"
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        cp "$COMPOSE_FILE" "$pre_rollback_backup/"
    fi
    
    docker-compose -f "$COMPOSE_FILE" config | grep "image:" > "$pre_rollback_backup/current_images.txt" 2>/dev/null || true
    
    # Stop current containers
    stop_current_containers
    
    # Restore configuration
    if ! restore_configuration "$backup_dir"; then
        log_error "Failed to restore configuration"
        exit 1
    fi
    
    # Restore database if requested
    if ! restore_database "$backup_dir" "$restore_db"; then
        log_error "Failed to restore database"
        exit 1
    fi
    
    # Start containers
    if ! start_containers; then
        log_error "Failed to start containers"
        exit 1
    fi
    
    # Health check
    if health_check "$HEALTH_CHECK_URL" "$HEALTH_CHECK_TIMEOUT" "$HEALTH_CHECK_INTERVAL"; then
        log_success "Rollback completed successfully!"
        send_notification "success" "Rollback completed successfully to $(basename "$backup_dir")"
        
        # Update last backup reference
        echo "$backup_dir" > .last_backup
    else
        log_error "Rollback failed health check"
        send_notification "error" "Rollback failed health check for $(basename "$backup_dir")"
        exit 1
    fi
}

# Main function
main() {
    local backup_dir=""
    local force="false"
    local restore_db="false"
    local list_only="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--backup-dir)
                backup_dir="$2"
                shift 2
                ;;
            -f|--force)
                force="true"
                shift
                ;;
            -d|--restore-database)
                restore_db="true"
                shift
                ;;
            -l|--list-backups)
                list_only="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # List backups if requested
    if [[ "$list_only" == "true" ]]; then
        list_backups
        exit 0
    fi
    
    # Get backup directory
    if ! backup_dir=$(get_backup_dir "$backup_dir"); then
        exit 1
    fi
    
    # Perform rollback
    perform_rollback "$backup_dir" "$force" "$restore_db"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi