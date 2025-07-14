# Internal PKI Structure for Cybersecurity Framework

## Overview
This PKI infrastructure provides secure certificate management for all framework services with load balancer certificate rotation support, compliance monitoring, and hierarchical certificate authority management.

## PKI Hierarchy Structure

```
Root CA (Offline - Air-gapped)
├── Intermediate CA 1 (Online - Infrastructure Services)
│   ├── Load Balancer CA (For LB certificate rotation)
│   ├── Service Mesh CA (For inter-service communication)
│   └── Gateway CA (For MCP gateway and API endpoints)
├── Intermediate CA 2 (Online - Agent Services)
│   ├── Agent Authentication CA
│   ├── Tool Registry CA
│   └── Database Access CA
└── Intermediate CA 3 (Online - External Integration)
    ├── Webhook CA (For external webhook verification)
    ├── API Client CA (For external API clients)
    └── SIEM Integration CA
```

## Directory Structure

```
pki/
├── root-ca/
│   ├── private/
│   │   └── root-ca.key              # Root CA private key (OFFLINE)
│   ├── certs/
│   │   ├── root-ca.crt              # Root CA certificate
│   │   └── root-ca-chain.crt        # Full chain certificate
│   ├── crl/
│   │   └── root-ca.crl              # Certificate Revocation List
│   └── config/
│       ├── root-ca.conf             # Root CA OpenSSL config
│       └── root-ca-policy.json      # CA policy configuration
│
├── intermediate-cas/
│   ├── infrastructure-ca/
│   │   ├── private/
│   │   │   └── infrastructure-ca.key
│   │   ├── certs/
│   │   │   ├── infrastructure-ca.crt
│   │   │   └── infrastructure-ca-chain.crt
│   │   ├── csr/
│   │   │   └── infrastructure-ca.csr
│   │   ├── crl/
│   │   │   └── infrastructure-ca.crl
│   │   └── config/
│   │       ├── infrastructure-ca.conf
│   │       └── policy.json
│   │
│   ├── agents-ca/
│   │   ├── private/
│   │   ├── certs/
│   │   ├── csr/
│   │   ├── crl/
│   │   └── config/
│   │
│   └── external-ca/
│       ├── private/
│       ├── certs/
│       ├── csr/
│       ├── crl/
│       └── config/
│
├── service-certificates/
│   ├── load-balancer/
│   │   ├── active/
│   │   │   ├── lb-current.key
│   │   │   ├── lb-current.crt
│   │   │   └── lb-current-chain.crt
│   │   ├── rotation/
│   │   │   ├── lb-next.key
│   │   │   ├── lb-next.crt
│   │   │   └── lb-next-chain.crt
│   │   └── backup/
│   │       ├── lb-backup-{timestamp}.key
│   │       ├── lb-backup-{timestamp}.crt
│   │       └── lb-backup-{timestamp}-chain.crt
│   │
│   ├── mcp-gateway/
│   │   ├── gateway-server.key
│   │   ├── gateway-server.crt
│   │   ├── gateway-client.key
│   │   └── gateway-client.crt
│   │
│   ├── agents/
│   │   ├── pki-agent/
│   │   │   ├── pki-agent.key
│   │   │   ├── pki-agent.crt
│   │   │   └── pki-agent-client.crt
│   │   ├── security-agent/
│   │   │   ├── security-agent.key
│   │   │   ├── security-agent.crt
│   │   │   └── security-agent-client.crt
│   │   ├── iam-agent/
│   │   │   ├── iam-agent.key
│   │   │   ├── iam-agent.crt
│   │   │   └── iam-agent-client.crt
│   │   ├── cissp-training-agent/
│   │   │   ├── cissp-agent.key
│   │   │   ├── cissp-agent.crt
│   │   │   └── cissp-agent-client.crt
│   │   └── audit-agent/
│   │       ├── audit-agent.key
│   │       ├── audit-agent.crt
│   │       └── audit-agent-client.crt
│   │
│   ├── infrastructure/
│   │   ├── vault/
│   │   │   ├── vault-server.key
│   │   │   ├── vault-server.crt
│   │   │   ├── vault-client.key
│   │   │   └── vault-client.crt
│   │   ├── postgres/
│   │   │   ├── postgres-server.key
│   │   │   ├── postgres-server.crt
│   │   │   ├── postgres-client.key
│   │   │   └── postgres-client.crt
│   │   ├── redis/
│   │   │   ├── redis-server.key
│   │   │   ├── redis-server.crt
│   │   │   ├── redis-client.key
│   │   │   └── redis-client.crt
│   │   └── monitoring/
│   │       ├── prometheus.key
│   │       ├── prometheus.crt
│   │       ├── grafana.key
│   │       └── grafana.crt
│   │
│   └── external-integrations/
│       ├── siem-integration/
│       │   ├── siem-client.key
│       │   ├── siem-client.crt
│       │   └── siem-webhook.crt
│       ├── ticketing-system/
│       │   ├── ticket-client.key
│       │   ├── ticket-client.crt
│       │   └── ticket-webhook.crt
│       └── api-endpoints/
│           ├── rest-api.key
│           ├── rest-api.crt
│           ├── graphql-api.key
│           ├── graphql-api.crt
│           ├── websocket-api.key
│           └── websocket-api.crt
│
├── trust-stores/
│   ├── agent-truststore.pem         # Trust store for all agents
│   ├── infrastructure-truststore.pem # Trust store for infrastructure
│   ├── external-truststore.pem      # Trust store for external services
│   └── full-chain-truststore.pem    # Complete trust chain
│
├── automation/
│   ├── scripts/
│   │   ├── generate-root-ca.sh
│   │   ├── generate-intermediate-ca.sh
│   │   ├── generate-service-cert.sh
│   │   ├── rotate-lb-cert.sh
│   │   ├── revoke-certificate.sh
│   │   └── update-crl.sh
│   ├── templates/
│   │   ├── root-ca.conf.template
│   │   ├── intermediate-ca.conf.template
│   │   ├── server-cert.conf.template
│   │   └── client-cert.conf.template
│   └── policies/
│       ├── certificate-policy.yaml
│       ├── rotation-policy.yaml
│       └── compliance-rules.yaml
│
└── compliance/
    ├── audit-logs/
    │   ├── certificate-issuance.log
    │   ├── certificate-revocation.log
    │   └── rotation-events.log
    ├── reports/
    │   ├── compliance-report-{date}.pdf
    │   ├── certificate-inventory.json
    │   └── expiration-dashboard.json
    └── monitoring/
        ├── cert-expiry-alerts.yaml
        ├── ca-health-checks.yaml
        └── rotation-status.yaml
```

## Certificate Types and Usage

### 1. Load Balancer Certificates (Hot Rotation Support)
- **Active Certificate**: Currently serving traffic
- **Next Certificate**: Pre-generated for seamless rotation
- **Backup Certificates**: Historical certificates for rollback
- **Rotation Schedule**: Automated daily/weekly rotation
- **DNS SANs**: Multiple domain names and IP addresses
- **Key Exchange**: Automated key exchange without service interruption

### 2. Service Mesh Certificates
- **mTLS Authentication**: Mutual TLS between all services
- **Service Identity**: Each service has unique certificate identity
- **Client Certificates**: For service-to-service authentication
- **Server Certificates**: For service endpoints

### 3. Agent Certificates
- **PKI Agent**: Manages certificate lifecycle
- **Security Agent**: Handles security scanning and monitoring
- **IAM Agent**: Identity and access management
- **CISSP Training Agent**: Security training and assessment
- **Audit Agent**: Compliance and audit logging

### 4. Infrastructure Certificates
- **Vault**: Secret management service
- **PostgreSQL**: Database with SSL/TLS
- **Redis**: Cache service with TLS
- **Monitoring**: Prometheus, Grafana with HTTPS

### 5. External Integration Certificates
- **SIEM Integration**: Secure SIEM connectivity
- **API Endpoints**: REST, GraphQL, WebSocket APIs
- **Webhook Verification**: Signed webhook payloads

## Security Features

### 1. Root CA Security
- **Offline Storage**: Root CA kept offline and air-gapped
- **HSM Integration**: Hardware Security Module support
- **Multi-person Authorization**: Require multiple operators for root operations
- **Secure Backup**: Encrypted backups in multiple locations

### 2. Certificate Rotation
- **Automated Rotation**: Scheduled certificate renewal
- **Zero-Downtime**: Load balancer hot certificate swapping
- **Rollback Capability**: Quick rollback to previous certificates
- **Health Monitoring**: Continuous certificate health checks

### 3. Compliance Monitoring
- **Certificate Inventory**: Real-time certificate tracking
- **Expiration Alerts**: Proactive expiration notifications
- **Audit Logging**: Complete audit trail of all PKI operations
- **Compliance Reports**: Automated compliance reporting

### 4. Access Control
- **Role-Based Access**: Different roles for PKI operations
- **Service Authentication**: mTLS for all inter-service communication
- **API Authentication**: Certificate-based API access
- **Audit Trail**: Complete logging of all access attempts

## Integration Points

### 1. Docker Compose Integration
```yaml
# Example service with PKI integration
services:
  pki-agent:
    image: cybersec-framework/pki-agent:latest
    volumes:
      - ./pki/service-certificates/agents/pki-agent:/etc/ssl/certs
      - ./pki/trust-stores:/etc/ssl/trust
    environment:
      - TLS_CERT_PATH=/etc/ssl/certs/pki-agent.crt
      - TLS_KEY_PATH=/etc/ssl/certs/pki-agent.key
      - CA_BUNDLE_PATH=/etc/ssl/trust/agent-truststore.pem
```

### 2. Vault Integration
- Store private keys in Vault
- Dynamic certificate generation
- Secret rotation automation
- Role-based certificate access

### 3. Monitoring Integration
- Certificate expiration monitoring
- PKI health dashboards
- Rotation status tracking
- Compliance metric collection

## Automation Workflows

### 1. Certificate Lifecycle
1. **Generation**: Automated certificate generation from templates
2. **Distribution**: Secure certificate distribution to services
3. **Rotation**: Scheduled certificate rotation
4. **Revocation**: Emergency certificate revocation
5. **Cleanup**: Automated cleanup of expired certificates

### 2. Load Balancer Rotation
1. **Pre-generation**: Generate next certificate 30 days before expiration
2. **Validation**: Validate new certificate before rotation
3. **Hot Swap**: Seamless certificate rotation without downtime
4. **Verification**: Post-rotation health checks
5. **Backup**: Archive previous certificate for rollback

### 3. Compliance Automation
1. **Inventory Scanning**: Regular certificate inventory updates
2. **Policy Enforcement**: Automated policy compliance checks
3. **Alert Generation**: Proactive alerts for policy violations
4. **Report Generation**: Automated compliance reports
5. **Remediation**: Automated remediation for common issues

This PKI structure provides enterprise-grade certificate management with automated rotation, compliance monitoring, and seamless integration with your cybersecurity framework's microservices architecture.
