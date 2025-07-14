# PKI Implementation Guide for Cybersecurity Framework

## Visual PKI Architecture

```
                                    ┌─────────────────┐
                                    │   Root CA       │
                                    │   (Offline)     │
                                    │                 │
                                    │ ✓ Air-gapped    │
                                    │ ✓ HSM protected │
                                    │ ✓ Multi-auth    │
                                    └─────────┬───────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     │                        │                        │
            ┌────────▼────────┐    ┌─────────▼─────────┐    ┌─────────▼─────────┐
            │ Infrastructure  │    │   Agent Services  │    │ External Integr.  │
            │ Intermediate CA │    │ Intermediate CA   │    │ Intermediate CA   │
            │                 │    │                   │    │                   │
            │ ✓ Load Balancer │    │ ✓ Agent Auth      │    │ ✓ API Clients     │
            │ ✓ Service Mesh  │    │ ✓ Tool Registry   │    │ ✓ Webhooks        │
            │ ✓ MCP Gateway   │    │ ✓ Database Access │    │ ✓ SIEM Integration│
            └────────┬────────┘    └─────────┬─────────┘    └─────────┬─────────┘
                     │                       │                        │
        ┌────────────┼─────────────┐         │               ┌────────┼────────┐
        │            │             │         │               │                 │
   ┌────▼───┐ ┌─────▼──┐ ┌────────▼──┐ ┌────▼───────┐ ┌─────▼──┐    ┌─────▼──┐
   │Load    │ │Service │ │MCP        │ │Agent       │ │External│    │API     │
   │Balancer│ │Mesh    │ │Gateway    │ │Services    │ │SIEM    │    │Clients │
   │Certs   │ │Certs   │ │Certs      │ │Certs       │ │Certs   │    │Certs   │
   └────────┘ └────────┘ └───────────┘ └────────────┘ └────────┘    └────────┘
```

## Service-to-Certificate Mapping

### Current Framework Services → PKI Integration

#### 1. Agent Services
```yaml
# PKI Agent (./agents/pki/pki_agent.py)
pki-agent:
  certificates:
    - pki-agent-server.crt     # For serving PKI management API
    - pki-agent-client.crt     # For authenticating to other services
  ca_authority: agents-ca
  rotation_schedule: "30 days"
  mtls_required: true

# Security Agent
security-agent:
  certificates:
    - security-agent-server.crt
    - security-agent-client.crt
  ca_authority: agents-ca
  special_permissions:
    - vault_access
    - database_audit

# IAM Agent
iam-agent:
  certificates:
    - iam-agent-server.crt
    - iam-agent-client.crt
  ca_authority: agents-ca
  privileged_access: true

# CISSP Training Agent
cissp-training-agent:
  certificates:
    - cissp-agent-server.crt
    - cissp-agent-client.crt
  ca_authority: agents-ca

# Audit Agent
audit-agent:
  certificates:
    - audit-agent-server.crt
    - audit-agent-client.crt
  ca_authority: agents-ca
  compliance_level: "high"
```

#### 2. Infrastructure Services (./infrastructure/)
```yaml
# Vault (./infrastructure/vault/)
vault:
  certificates:
    - vault-server.crt         # TLS endpoint
    - vault-client.crt         # Client authentication
  ca_authority: infrastructure-ca
  high_security: true
  key_storage: hsm

# PostgreSQL (./infrastructure/postgres/)
postgres:
  certificates:
    - postgres-server.crt
    - postgres-client.crt
  ca_authority: infrastructure-ca
  ssl_mode: require

# Redis
redis:
  certificates:
    - redis-server.crt
    - redis-client.crt
  ca_authority: infrastructure-ca

# MCP Server (./infrastructure/mcp-server/)
mcp-gateway:
  certificates:
    - gateway-server.crt       # For agent connections
    - gateway-client.crt       # For external integrations
  ca_authority: infrastructure-ca
  load_balancer_backend: true
```

#### 3. Load Balancer Configuration
```yaml
# Load Balancer (Hot Certificate Rotation)
load-balancer:
  active_certificates:
    - lb-current.crt
    - lb-current-chain.crt
  rotation_certificates:
    - lb-next.crt             # Pre-generated for seamless swap
    - lb-next-chain.crt
  backup_certificates:
    - lb-backup-*.crt         # Historical backups
  ca_authority: infrastructure-ca/load-balancer-ca
  rotation_trigger: "24 hours before expiry"
  dns_sans:
    - "cybersec-framework.local"
    - "api.cybersec-framework.local"
    - "*.cybersec-framework.local"
    - "127.0.0.1"
    - "localhost"
```

## Docker Compose Integration

### Updated docker-compose.yml with PKI
```yaml
# Extending your existing ./infrastructure/docker-compose.yml
version: '3.8'

services:
  # PKI Certificate Authority
  pki-ca:
    image: cybersec-framework/pki-ca:latest
    container_name: pki-ca
    volumes:
      - ./pki:/pki
      - ca_data:/var/lib/ca
    environment:
      - CA_MODE=intermediate
      - ROOT_CA_PATH=/pki/root-ca/certs/root-ca.crt
    networks:
      - cybersec-internal

  # Load Balancer with certificate rotation
  load-balancer:
    image: haproxy:2.8-alpine
    container_name: cybersec-lb
    ports:
      - "80:80"
      - "443:443"
      - "8404:8404"  # Stats page
    volumes:
      - ./pki/service-certificates/load-balancer:/etc/ssl/certs:ro
      - ./configs/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    environment:
      - CERT_ROTATION_ENABLED=true
      - CERT_CHECK_INTERVAL=3600
    depends_on:
      - pki-ca
    networks:
      - cybersec-public
      - cybersec-internal

  # PKI Agent Service
  pki-agent:
    image: cybersec-framework/pki-agent:latest
    container_name: pki-agent
    volumes:
      - ./pki/service-certificates/agents/pki-agent:/etc/ssl/certs:ro
      - ./pki/trust-stores:/etc/ssl/trust:ro
    environment:
      - TLS_CERT_PATH=/etc/ssl/certs/pki-agent.crt
      - TLS_KEY_PATH=/etc/ssl/certs/pki-agent.key
      - CA_BUNDLE_PATH=/etc/ssl/trust/agent-truststore.pem
      - MCP_GATEWAY_URL=https://mcp-gateway:8443
    depends_on:
      - pki-ca
      - vault
    networks:
      - cybersec-internal

  # Vault with TLS
  vault:
    image: hashicorp/vault:latest
    container_name: vault
    volumes:
      - ./pki/service-certificates/infrastructure/vault:/etc/ssl/certs:ro
      - vault_data:/vault/data
    environment:
      - VAULT_ADDR=https://0.0.0.0:8200
      - VAULT_API_ADDR=https://vault:8200
      - VAULT_TLS_CERT_FILE=/etc/ssl/certs/vault-server.crt
      - VAULT_TLS_KEY_FILE=/etc/ssl/certs/vault-server.key
    command: vault server -config=/vault/config/vault.hcl
    depends_on:
      - pki-ca
    networks:
      - cybersec-internal

  # PostgreSQL with SSL
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    volumes:
      - ./pki/service-certificates/infrastructure/postgres:/etc/ssl/certs:ro
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_SSL_CERT_FILE=/etc/ssl/certs/postgres-server.crt
      - POSTGRES_SSL_KEY_FILE=/etc/ssl/certs/postgres-server.key
      - POSTGRES_SSL_CA_FILE=/etc/ssl/certs/postgres-ca.crt
      - POSTGRES_SSL_MODE=require
    command: postgres -c ssl=on -c ssl_cert_file=/etc/ssl/certs/postgres-server.crt -c ssl_key_file=/etc/ssl/certs/postgres-server.key
    depends_on:
      - pki-ca
    networks:
      - cybersec-internal

  # MCP Gateway with TLS
  mcp-gateway:
    image: cybersec-framework/mcp-gateway:latest
    container_name: mcp-gateway
    volumes:
      - ./pki/service-certificates/mcp-gateway:/etc/ssl/certs:ro
      - ./pki/trust-stores:/etc/ssl/trust:ro
    environment:
      - TLS_CERT_PATH=/etc/ssl/certs/gateway-server.crt
      - TLS_KEY_PATH=/etc/ssl/certs/gateway-server.key
      - CLIENT_CA_PATH=/etc/ssl/trust/agent-truststore.pem
      - MTLS_REQUIRED=true
    ports:
      - "8443:8443"
    depends_on:
      - pki-ca
    networks:
      - cybersec-internal

volumes:
  ca_data:
  vault_data:
  postgres_data:

networks:
  cybersec-public:
    driver: bridge
  cybersec-internal:
    driver: bridge
    internal: true
```

## Certificate Rotation Automation

### Load Balancer Hot Rotation Script
```bash
#!/bin/bash
# ./pki/automation/scripts/rotate-lb-cert.sh

set -euo pipefail

LB_CERT_DIR="/pki/service-certificates/load-balancer"
CURRENT_CERT="$LB_CERT_DIR/active/lb-current.crt"
NEXT_CERT="$LB_CERT_DIR/rotation/lb-next.crt"
BACKUP_DIR="$LB_CERT_DIR/backup"

# Function to perform hot certificate swap
rotate_certificate() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    # 1. Backup current certificate
    echo "Backing up current certificate..."
    cp "$LB_CERT_DIR/active/"* "$BACKUP_DIR/backup_$timestamp/"
    
    # 2. Validate next certificate
    echo "Validating next certificate..."
    openssl x509 -in "$NEXT_CERT" -noout -checkend 86400
    
    # 3. Signal load balancer to reload (HAProxy graceful reload)
    echo "Performing graceful certificate rotation..."
    docker exec cybersec-lb sh -c '
        # Move next cert to active
        mv /etc/ssl/certs/rotation/* /etc/ssl/certs/active/
        # Graceful reload without dropping connections
        kill -USR2 $(cat /var/run/haproxy.pid)
    '
    
    # 4. Generate new "next" certificate for future rotation
    echo "Generating new next certificate..."
    ./generate-service-cert.sh load-balancer-next
    
    echo "Certificate rotation completed successfully!"
}

# Check if rotation is needed (certificate expires within 24 hours)
if openssl x509 -in "$CURRENT_CERT" -noout -checkend 86400; then
    echo "Current certificate is still valid for more than 24 hours"
    exit 0
else
    echo "Certificate expires within 24 hours, rotating..."
    rotate_certificate
fi
```

## Monitoring and Compliance

### Certificate Expiry Monitoring
```yaml
# ./pki/compliance/monitoring/cert-expiry-alerts.yaml
alerts:
  - name: certificate_expiring_soon
    expr: (cert_expiry_timestamp - time()) / 86400 < 30
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Certificate expiring in {{ $value }} days"
      description: "Certificate {{ $labels.cert_name }} will expire in {{ $value }} days"

  - name: certificate_expiring_critical
    expr: (cert_expiry_timestamp - time()) / 86400 < 7
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Certificate expiring in {{ $value }} days - URGENT"
      description: "Certificate {{ $labels.cert_name }} will expire in {{ $value }} days"

  - name: load_balancer_cert_rotation_failed
    expr: lb_cert_rotation_success == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Load balancer certificate rotation failed"
      description: "Automatic certificate rotation for load balancer has failed"
```

## Security Best Practices Implemented

1. **Zero-Trust Architecture**: All services require mTLS authentication
2. **Principle of Least Privilege**: Each service has minimal certificate permissions
3. **Defense in Depth**: Multiple CA layers with different security levels
4. **Continuous Monitoring**: Real-time certificate health monitoring
5. **Automated Recovery**: Automatic rollback on failed rotations
6. **Compliance Logging**: Complete audit trail of all PKI operations
7. **Air-Gapped Root CA**: Offline root CA for maximum security
8. **Hot Certificate Rotation**: Zero-downtime certificate updates

This PKI implementation provides enterprise-grade security while maintaining the flexibility and scalability needed for your cybersecurity framework's microservices architecture.
