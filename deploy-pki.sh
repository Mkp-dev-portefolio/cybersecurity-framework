#!/bin/bash
# Enterprise PKI Deployment Script
# CyberSec Framework - Dual Root CA with Cross-Certification

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="vault-pki-compose.yml"
ENV_FILE=".env.pki"
PROJECT_NAME="cybersec-pki"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed or not in PATH"
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    log "Creating PKI directory structure..."
    
    # Make sure all directories exist with proper permissions
    find vault-pki -type d -exec chmod 755 {} \;
    find vault-pki -name "*.sh" -exec chmod +x {} \;
    
    success "Directory structure created"
}

# Generate initial certificates (self-signed for development)
generate_initial_certs() {
    log "Generating initial self-signed certificates for development..."
    
    CERTS_DIR="vault-pki/service-certificates/tls/services/vault-server"
    mkdir -p "$CERTS_DIR"
    
    # Generate CA certificate
    openssl genrsa -out "$CERTS_DIR/vault-ca.key" 4096
    openssl req -new -x509 -days 365 -key "$CERTS_DIR/vault-ca.key" \
        -out "$CERTS_DIR/vault-ca.crt" \
        -subj "/C=US/ST=CA/L=San Francisco/O=CyberSec Framework/OU=PKI/CN=Vault CA"
    
    # Generate server certificate
    openssl genrsa -out "$CERTS_DIR/vault-server.key" 4096
    openssl req -new -key "$CERTS_DIR/vault-server.key" \
        -out "$CERTS_DIR/vault-server.csr" \
        -subj "/C=US/ST=CA/L=San Francisco/O=CyberSec Framework/OU=PKI/CN=vault"
    
    # Create extensions file
    cat > "$CERTS_DIR/vault-server.ext" << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = vault
DNS.2 = localhost
DNS.3 = cybersec-vault-pki
IP.1 = 127.0.0.1
IP.2 = 172.20.0.2
EOF
    
    # Sign server certificate
    openssl x509 -req -in "$CERTS_DIR/vault-server.csr" \
        -CA "$CERTS_DIR/vault-ca.crt" \
        -CAkey "$CERTS_DIR/vault-ca.key" \
        -CAcreateserial \
        -out "$CERTS_DIR/vault-server.crt" \
        -days 365 \
        -extfile "$CERTS_DIR/vault-server.ext"
    
    # Set permissions
    chmod 600 "$CERTS_DIR"/*.key
    chmod 644 "$CERTS_DIR"/*.crt
    
    # Clean up
    rm "$CERTS_DIR/vault-server.csr" "$CERTS_DIR/vault-server.ext"
    
    success "Initial certificates generated"
}

# Deploy the PKI infrastructure
deploy_infrastructure() {
    log "Deploying PKI infrastructure..."
    
    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi
    
    # Deploy with Docker Compose
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    
    success "PKI infrastructure deployed"
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."
    
    # Wait for Vault
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T vault vault status &> /dev/null; then
            break
        fi
        
        log "Waiting for Vault... (attempt $attempt/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "Vault failed to start within expected time"
    fi
    
    success "Services are ready"
}

# Display status and next steps
show_status() {
    log "Getting deployment status..."
    
    echo
    echo "🚀 Enterprise PKI Infrastructure Status:"
    echo "========================================"
    
    # Show running containers
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    
    echo
    echo "📋 Access Information:"
    echo "--------------------"
    echo "• Vault UI: https://localhost:8200"
    echo "• PKI Manager: http://localhost:8080"
    echo "• Metrics: http://localhost:9100"
    echo "• PostgreSQL: localhost:5432 (pki_audit database)"
    echo "• Redis: localhost:6379"
    
    echo
    echo "🔐 Security Information:"
    echo "----------------------"
    echo "• Vault token: Check vault-init container logs or /vault-init/vault-token"
    echo "• Postgres password: $POSTGRES_PASSWORD"
    echo "• Redis password: $REDIS_PASSWORD"
    
    echo
    echo "📁 Important Directories:"
    echo "------------------------"
    echo "• PKI structure: ./vault-pki/"
    echo "• Vault data: Docker volume 'vault_data'"
    echo "• Vault logs: Docker volume 'vault_logs'"
    echo "• Certificates: ./vault-pki/service-certificates/"
    
    echo
    echo "🔧 Next Steps:"
    echo "-------------"
    echo "1. Check Vault initialization: docker logs cybersec-pki_vault-init_1"
    echo "2. Access Vault UI and review PKI mounts"
    echo "3. Generate and sign intermediate CA certificates"
    echo "4. Configure certificate roles and policies"
    echo "5. Set up automated certificate issuance"
    
    success "PKI deployment completed successfully! 🎉"
}

# Cleanup function
cleanup() {
    log "Cleaning up PKI infrastructure..."
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down -v
    success "Cleanup completed"
}

# Show help
show_help() {
    echo "Enterprise PKI Deployment Script"
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  deploy    Deploy the PKI infrastructure (default)"
    echo "  status    Show deployment status"
    echo "  logs      Show service logs"
    echo "  cleanup   Remove all PKI services and volumes"
    echo "  help      Show this help message"
    echo
    echo "Environment file: $ENV_FILE"
    echo "Compose file: $COMPOSE_FILE"
}

# Main execution
main() {
    local action="${1:-deploy}"
    
    case "$action" in
        "deploy")
            log "Starting Enterprise PKI deployment..."
            check_prerequisites
            create_directories
            generate_initial_certs
            deploy_infrastructure
            wait_for_services
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Unknown action: $action. Use 'help' for usage information."
            ;;
    esac
}

# Run main function
main "$@"
