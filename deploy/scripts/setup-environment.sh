#!/bin/bash

# Environment Setup Script for Django GraphQL Auto System
# This script prepares a server for deployment

set -euo pipefail

# Configuration
DOCKER_COMPOSE_VERSION="2.21.0"
NGINX_VERSION="1.24"
POSTGRES_VERSION="15"
REDIS_VERSION="7"

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

Setup environment for Django GraphQL Auto System deployment

OPTIONS:
    -e, --environment ENV   Environment type (staging|production) [default: staging]
    -u, --user USER         Application user [default: django]
    -d, --directory DIR     Application directory [default: /opt/django-graphql]
    -s, --ssl               Setup SSL certificates
    -m, --monitoring        Setup monitoring stack
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Setup staging environment
    $0 -e production -s -m  # Setup production with SSL and monitoring
    $0 -u myuser -d /app    # Custom user and directory

EOF
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        log_info "Please run as a regular user with sudo privileges"
        exit 1
    fi
    
    # Check sudo access
    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo privileges"
        exit 1
    fi
}

# Detect operating system
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        log_error "Cannot detect operating system"
        exit 1
    fi
    
    log_info "Detected OS: $OS $OS_VERSION"
    
    case $OS in
        ubuntu|debian)
            PACKAGE_MANAGER="apt"
            ;;
        centos|rhel|fedora)
            PACKAGE_MANAGER="yum"
            ;;
        *)
            log_error "Unsupported operating system: $OS"
            exit 1
            ;;
    esac
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    
    case $PACKAGE_MANAGER in
        apt)
            sudo apt update
            sudo apt upgrade -y
            sudo apt install -y curl wget git unzip software-properties-common
            ;;
        yum)
            sudo yum update -y
            sudo yum install -y curl wget git unzip epel-release
            ;;
    esac
    
    log_success "System packages updated"
}

# Install Docker
install_docker() {
    log_info "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed"
        docker --version
        return 0
    fi
    
    case $PACKAGE_MANAGER in
        apt)
            # Add Docker's official GPG key
            curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Add Docker repository
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker
            sudo apt update
            sudo apt install -y docker-ce docker-ce-cli containerd.io
            ;;
        yum)
            # Add Docker repository
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # Install Docker
            sudo yum install -y docker-ce docker-ce-cli containerd.io
            ;;
    esac
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    log_success "Docker installed successfully"
    log_warning "Please log out and log back in for Docker group changes to take effect"
}

# Install Docker Compose
install_docker_compose() {
    log_info "Installing Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose is already installed"
        docker-compose --version
        return 0
    fi
    
    # Download and install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create symlink for easier access
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose installed successfully"
    docker-compose --version
}

# Create application user
create_app_user() {
    local app_user="$1"
    
    log_info "Creating application user: $app_user"
    
    if id "$app_user" &>/dev/null; then
        log_info "User $app_user already exists"
        return 0
    fi
    
    # Create user with home directory
    sudo useradd -m -s /bin/bash "$app_user"
    
    # Add user to docker group
    sudo usermod -aG docker "$app_user"
    
    # Create SSH directory
    sudo mkdir -p "/home/$app_user/.ssh"
    sudo chown "$app_user:$app_user" "/home/$app_user/.ssh"
    sudo chmod 700 "/home/$app_user/.ssh"
    
    log_success "Application user $app_user created"
}

# Setup application directory
setup_app_directory() {
    local app_dir="$1"
    local app_user="$2"
    
    log_info "Setting up application directory: $app_dir"
    
    # Create application directory
    sudo mkdir -p "$app_dir"
    sudo chown "$app_user:$app_user" "$app_dir"
    sudo chmod 755 "$app_dir"
    
    # Create subdirectories
    local subdirs=("logs" "backups" "ssl" "data" "static" "media")
    for subdir in "${subdirs[@]}"; do
        sudo mkdir -p "$app_dir/$subdir"
        sudo chown "$app_user:$app_user" "$app_dir/$subdir"
    done
    
    # Set proper permissions
    sudo chmod 750 "$app_dir/logs"
    sudo chmod 700 "$app_dir/backups"
    sudo chmod 700 "$app_dir/ssl"
    sudo chmod 755 "$app_dir/data"
    sudo chmod 755 "$app_dir/static"
    sudo chmod 755 "$app_dir/media"
    
    log_success "Application directory structure created"
}

# Install Nginx
install_nginx() {
    log_info "Installing Nginx..."
    
    if command -v nginx &> /dev/null; then
        log_info "Nginx is already installed"
        nginx -v
        return 0
    fi
    
    case $PACKAGE_MANAGER in
        apt)
            sudo apt install -y nginx
            ;;
        yum)
            sudo yum install -y nginx
            ;;
    esac
    
    # Start and enable Nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    # Configure firewall
    if command -v ufw &> /dev/null; then
        sudo ufw allow 'Nginx Full'
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        sudo firewall-cmd --reload
    fi
    
    log_success "Nginx installed and configured"
}

# Setup SSL certificates
setup_ssl() {
    local app_dir="$1"
    local domain="$2"
    
    log_info "Setting up SSL certificates..."
    
    # Install Certbot
    case $PACKAGE_MANAGER in
        apt)
            sudo apt install -y certbot python3-certbot-nginx
            ;;
        yum)
            sudo yum install -y certbot python3-certbot-nginx
            ;;
    esac
    
    if [[ -n "$domain" && "$domain" != "localhost" ]]; then
        # Get Let's Encrypt certificate
        log_info "Obtaining SSL certificate for $domain..."
        sudo certbot --nginx -d "$domain" --non-interactive --agree-tos --email admin@"$domain"
        
        # Setup auto-renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
    else
        # Generate self-signed certificate for development
        log_info "Generating self-signed SSL certificate..."
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$app_dir/ssl/key.pem" \
            -out "$app_dir/ssl/cert.pem" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        sudo chown root:root "$app_dir/ssl/"*.pem
        sudo chmod 600 "$app_dir/ssl/"*.pem
    fi
    
    log_success "SSL certificates configured"
}

# Setup monitoring stack
setup_monitoring() {
    local app_dir="$1"
    
    log_info "Setting up monitoring stack..."
    
    # Create monitoring configuration directory
    sudo mkdir -p "$app_dir/monitoring"
    
    # Create Prometheus configuration
    cat > /tmp/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'django-app'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
EOF
    
    sudo mv /tmp/prometheus.yml "$app_dir/monitoring/"
    
    # Create Grafana provisioning
    sudo mkdir -p "$app_dir/monitoring/grafana/provisioning/datasources"
    sudo mkdir -p "$app_dir/monitoring/grafana/provisioning/dashboards"
    
    cat > /tmp/datasources.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    
    sudo mv /tmp/datasources.yml "$app_dir/monitoring/grafana/provisioning/datasources/"
    
    log_success "Monitoring stack configured"
}

# Setup log rotation
setup_log_rotation() {
    local app_dir="$1"
    
    log_info "Setting up log rotation..."
    
    cat > /tmp/django-graphql << EOF
$app_dir/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 django django
    postrotate
        docker-compose -f $app_dir/docker-compose.production.yml restart web
    endscript
}
EOF
    
    sudo mv /tmp/django-graphql /etc/logrotate.d/
    sudo chmod 644 /etc/logrotate.d/django-graphql
    
    log_success "Log rotation configured"
}

# Setup system monitoring
setup_system_monitoring() {
    log_info "Setting up system monitoring..."
    
    # Install system monitoring tools
    case $PACKAGE_MANAGER in
        apt)
            sudo apt install -y htop iotop nethogs ncdu
            ;;
        yum)
            sudo yum install -y htop iotop nethogs ncdu
            ;;
    esac
    
    # Setup system limits
    cat > /tmp/django-limits.conf << 'EOF'
django soft nofile 65536
django hard nofile 65536
django soft nproc 32768
django hard nproc 32768
EOF
    
    sudo mv /tmp/django-limits.conf /etc/security/limits.d/
    
    log_success "System monitoring configured"
}

# Create deployment scripts
create_deployment_scripts() {
    local app_dir="$1"
    local app_user="$2"
    
    log_info "Creating deployment scripts..."
    
    # Create scripts directory
    sudo mkdir -p "$app_dir/scripts"
    
    # Create start script
    cat > /tmp/start.sh << 'EOF'
#!/bin/bash
cd /opt/django-graphql
docker-compose -f docker-compose.production.yml up -d
EOF
    
    # Create stop script
    cat > /tmp/stop.sh << 'EOF'
#!/bin/bash
cd /opt/django-graphql
docker-compose -f docker-compose.production.yml down
EOF
    
    # Create status script
    cat > /tmp/status.sh << 'EOF'
#!/bin/bash
cd /opt/django-graphql
docker-compose -f docker-compose.production.yml ps
EOF
    
    # Move scripts and set permissions
    sudo mv /tmp/start.sh "$app_dir/scripts/"
    sudo mv /tmp/stop.sh "$app_dir/scripts/"
    sudo mv /tmp/status.sh "$app_dir/scripts/"
    
    sudo chown "$app_user:$app_user" "$app_dir/scripts/"*.sh
    sudo chmod +x "$app_dir/scripts/"*.sh
    
    log_success "Deployment scripts created"
}

# Main setup function
main() {
    local environment="staging"
    local app_user="django"
    local app_dir="/opt/django-graphql"
    local setup_ssl="false"
    local setup_monitoring_flag="false"
    local domain=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                environment="$2"
                shift 2
                ;;
            -u|--user)
                app_user="$2"
                shift 2
                ;;
            -d|--directory)
                app_dir="$2"
                shift 2
                ;;
            -s|--ssl)
                setup_ssl="true"
                shift
                ;;
            -m|--monitoring)
                setup_monitoring_flag="true"
                shift
                ;;
            --domain)
                domain="$2"
                shift 2
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
    
    log_info "Starting environment setup..."
    log_info "Environment: $environment"
    log_info "User: $app_user"
    log_info "Directory: $app_dir"
    
    # Pre-flight checks
    check_root
    detect_os
    
    # System setup
    update_system
    install_docker
    install_docker_compose
    install_nginx
    
    # Application setup
    create_app_user "$app_user"
    setup_app_directory "$app_dir" "$app_user"
    
    # Optional components
    if [[ "$setup_ssl" == "true" ]]; then
        setup_ssl "$app_dir" "$domain"
    fi
    
    if [[ "$setup_monitoring_flag" == "true" ]]; then
        setup_monitoring "$app_dir"
    fi
    
    # System configuration
    setup_log_rotation "$app_dir"
    setup_system_monitoring
    create_deployment_scripts "$app_dir" "$app_user"
    
    log_success "Environment setup completed successfully!"
    log_info "Next steps:"
    log_info "1. Log out and log back in to apply Docker group changes"
    log_info "2. Copy your application files to $app_dir"
    log_info "3. Configure environment variables"
    log_info "4. Run your deployment script"
    
    if [[ "$setup_ssl" == "true" && -z "$domain" ]]; then
        log_warning "Self-signed SSL certificate created. For production, use a real domain and Let's Encrypt"
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi