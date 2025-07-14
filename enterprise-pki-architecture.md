# Enterprise PKI Architecture for Cybersecurity Framework

## Executive Summary
This PKI design follows enterprise security best practices with dual root Certificate Authorities (CAs), dedicated intermediate CAs for different certificate types, and specific Extended Key Usage (EKU) configurations for agents. The entire PKI is built on HashiCorp Vault running locally in Docker containers.

## Dual Root CA Architecture with Cross-Certification

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE PKI HIERARCHY (Single Vault)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐    ◄──Cross Cert──►   ┌─────────────────────┐     │
│  │   PRIMARY ROOT CA   │                        │  SECONDARY ROOT CA  │     │
│  │   (Offline/HSM)     │                        │   (Offline/HSM)     │     │
│  │                     │                        │                     │     │
│  │ • TLS Certificates  │                        │ • Code Signing      │     │
│  │ • Authentication    │                        │ • Time Stamping     │     │
│  │ • Server Identity   │                        │ • Document Signing  │     │
│  │ • Client Identity   │                        │ • Agent Attestation │     │
│  └──────────┬──────────┘                        └──────────┬──────────┘     │
│             │                                              │               │
│             └─────────────────┐      ┌─────────────────────┘               │
│                               ▼      ▼                                     │
│                    ┌─────────────────────────┐                            │
│                    │   SINGLE VAULT PKI      │                            │
│                    │   (All Intermediate     │                            │
│                    │    CAs in one vault)    │                            │
│                    └──────────┬──────────────┘                            │
│                               │                                            │
│              ┌────────────────┼────────────────┐                          │
│              │                │                │                          │
│              ▼                ▼                ▼                          │
│        ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐     │
│        │   TLS   │      │  AUTH   │      │CODE SIGN│      │ AGENT   │     │
│        │ INTER.  │      │ INTER.  │      │ INTER.  │      │ INTER.  │     │
│        │   CA    │      │   CA    │      │   CA    │      │   CA    │     │
│        │/tls-ca  │      │/auth-ca │      │/code-ca │      │/agent-ca│     │
│        └─────────┘      └─────────┘      └─────────┘      └─────────┘     │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Detailed PKI Structure

### Root Certificate Authorities

#### 1. Primary Root CA (TLS & Authentication)
```yaml
primary_root_ca:
  name: "CyberSec Framework Primary Root CA"
  key_algorithm: RSA
  key_size: 4096
  validity: 20 years
  storage: offline/hsm
  purpose:
    - TLS server authentication
    - TLS client authentication
    - Server identity verification
    - Client identity verification
  key_usage:
    - digital_signature
    - key_cert_sign
    - crl_sign
  basic_constraints:
    ca: true
    path_length: 2
```

#### 2. Secondary Root CA (Code Signing & Agent Attestation)
```yaml
secondary_root_ca:
  name: "CyberSec Framework Code Signing Root CA"
  key_algorithm: RSA
  key_size: 4096
  validity: 20 years
  storage: offline/hsm
  purpose:
    - Code signing
    - Agent binary attestation
    - Document signing
    - Time stamping
  key_usage:
    - digital_signature
    - key_cert_sign
    - crl_sign
  basic_constraints:
    ca: true
    path_length: 2
```

#### 3. Cross-Certification Configuration
```yaml
cross_certification:
  purpose: "Enable mutual trust between the two root CAs"
  configuration:
    primary_signs_secondary:
      issuer: "CyberSec Framework Primary Root CA"
      subject: "CyberSec Framework Code Signing Root CA"
      validity: 10 years
      key_usage:
        - digital_signature
        - key_cert_sign
      path_length_constraint: 1
      
    secondary_signs_primary:
      issuer: "CyberSec Framework Code Signing Root CA"
      subject: "CyberSec Framework Primary Root CA"
      validity: 10 years
      key_usage:
        - digital_signature
        - key_cert_sign
      path_length_constraint: 1
      
  benefits:
    - Enables certificate path validation from either root
    - Provides redundancy in case one root becomes unavailable
    - Allows seamless certificate validation across certificate types
    - Supports policy flexibility for different use cases
```

### Intermediate Certificate Authorities (Online - Vault)

#### 1. TLS Intermediate CA
```yaml
tls_intermediate_ca:
  parent: primary_root_ca
  name: "CyberSec Framework TLS Intermediate CA"
  validity: 10 years
  vault_mount: "tls-ca"
  certificate_types:
    - Server TLS certificates
    - Load balancer certificates
    - Service mesh certificates
    - API endpoint certificates
  key_usage:
    - digital_signature
    - key_encipherment
    - key_cert_sign
    - crl_sign
  extended_key_usage:
    - server_auth
    - client_auth
```

#### 2. Authentication Intermediate CA
```yaml
auth_intermediate_ca:
  parent: primary_root_ca
  name: "CyberSec Framework Authentication Intermediate CA"
  validity: 10 years
  vault_mount: "auth-ca"
  certificate_types:
    - User authentication certificates
    - Service authentication certificates
    - mTLS client certificates
    - API client certificates
  key_usage:
    - digital_signature
    - key_encipherment
    - key_cert_sign
    - crl_sign
  extended_key_usage:
    - client_auth
    - email_protection
```

#### 3. Code Signing Intermediate CA
```yaml
code_signing_intermediate_ca:
  parent: secondary_root_ca
  name: "CyberSec Framework Code Signing Intermediate CA"
  validity: 5 years
  vault_mount: "code-signing-ca"
  certificate_types:
    - Agent binary signing
    - Container image signing
    - Configuration signing
    - Update package signing
  key_usage:
    - digital_signature
    - key_cert_sign
    - crl_sign
  extended_key_usage:
    - code_signing
```

#### 4. Agent Attestation Intermediate CA
```yaml
agent_attestation_intermediate_ca:
  parent: secondary_root_ca
  name: "CyberSec Framework Agent Attestation Intermediate CA"
  validity: 5 years
  vault_mount: "agent-attestation-ca"
  certificate_types:
    - Agent identity certificates
    - Agent capability certificates
    - Tool registry certificates
    - MCP protocol certificates
  key_usage:
    - digital_signature
    - key_encipherment
    - key_cert_sign
    - crl_sign
  extended_key_usage:
    - client_auth
    - 1.3.6.1.4.1.311.10.3.13  # Lifetime Signing EKU
    - 1.3.6.1.4.1.311.10.3.24  # Windows Store EKU (for attestation)
```

## Directory Structure

```
vault-pki/
├── config/
│   ├── vault-config.hcl
│   ├── policies/
│   │   ├── tls-ca-policy.hcl
│   │   ├── auth-ca-policy.hcl
│   │   ├── code-signing-policy.hcl
│   │   └── agent-attestation-policy.hcl
│   └── roles/
│       ├── tls-server-role.json
│       ├── tls-client-role.json
│       ├── auth-client-role.json
│       ├── code-signing-role.json
│       └── agent-attestation-role.json
│
├── root-cas/
│   ├── primary-root/
│   │   ├── private/
│   │   │   └── primary-root-ca.key  # OFFLINE STORAGE
│   │   ├── certs/
│   │   │   ├── primary-root-ca.crt
│   │   │   ├── primary-root-ca-chain.pem
│   │   │   └── primary-signed-by-secondary.crt  # Cross-cert
│   │   └── config/
│   │       ├── openssl.cnf
│   │       └── policy.json
│   │
│   ├── secondary-root/
│   │   ├── private/
│   │   │   └── secondary-root-ca.key  # OFFLINE STORAGE
│   │   ├── certs/
│   │   │   ├── secondary-root-ca.crt
│   │   │   ├── secondary-root-ca-chain.pem
│   │   │   └── secondary-signed-by-primary.crt  # Cross-cert
│   │   └── config/
│   │       ├── openssl.cnf
│   │       └── policy.json
│   │
│   └── cross-certificates/
│       ├── primary-to-secondary-cross.crt
│       ├── secondary-to-primary-cross.crt
│       ├── combined-trust-chain.pem
│       └── cross-cert-validation.log
│
├── intermediate-cas/
│   ├── tls-intermediate/
│   │   ├── signed-cert/
│   │   │   └── tls-intermediate-ca.crt
│   │   └── chain/
│   │       └── tls-intermediate-chain.pem
│   │
│   ├── auth-intermediate/
│   │   ├── signed-cert/
│   │   │   └── auth-intermediate-ca.crt
│   │   └── chain/
│   │       └── auth-intermediate-chain.pem
│   │
│   ├── code-signing-intermediate/
│   │   ├── signed-cert/
│   │   │   └── code-signing-intermediate-ca.crt
│   │   └── chain/
│   │       └── code-signing-intermediate-chain.pem
│   │
│   └── agent-attestation-intermediate/
│       ├── signed-cert/
│       │   └── agent-attestation-intermediate-ca.crt
│       └── chain/
│           └── agent-attestation-intermediate-chain.pem
│
├── service-certificates/
│   ├── tls/
│   │   ├── load-balancer/
│   │   │   ├── active/
│   │   │   ├── rotation/
│   │   │   └── backup/
│   │   ├── services/
│   │   │   ├── vault-server/
│   │   │   ├── postgres-server/
│   │   │   ├── redis-server/
│   │   │   ├── mcp-gateway/
│   │   │   └── monitoring/
│   │   └── agents/
│   │       ├── pki-agent/
│   │       ├── security-agent/
│   │       ├── iam-agent/
│   │       ├── cissp-training-agent/
│   │       └── audit-agent/
│   │
│   ├── auth/
│   │   ├── client-certificates/
│   │   │   ├── agents/
│   │   │   ├── services/
│   │   │   └── external-clients/
│   │   └── user-certificates/
│   │       ├── administrators/
│   │       ├── operators/
│   │       └── readonly-users/
│   │
│   ├── code-signing/
│   │   ├── agent-binaries/
│   │   ├── container-images/
│   │   ├── configuration-files/
│   │   └── update-packages/
│   │
│   └── agent-attestation/
│       ├── pki-agent-identity/
│       ├── security-agent-identity/
│       ├── iam-agent-identity/
│       ├── cissp-training-agent-identity/
│       ├── audit-agent-identity/
│       └── tool-registry/
│
├── trust-stores/
│   ├── tls-truststore.pem
│   ├── auth-truststore.pem
│   ├── code-signing-truststore.pem
│   ├── agent-attestation-truststore.pem
│   └── complete-chain-truststore.pem
│
├── automation/
│   ├── vault-scripts/
│   │   ├── setup-vault-pki.sh
│   │   ├── configure-ca-mounts.sh
│   │   ├── setup-roles.sh
│   │   ├── issue-certificate.sh
│   │   ├── revoke-certificate.sh
│   │   └── rotate-intermediate-ca.sh
│   │
│   ├── templates/
│   │   ├── vault-policy.hcl.template
│   │   ├── certificate-role.json.template
│   │   └── openssl.cnf.template
│   │
│   └── monitoring/
│       ├── cert-expiry-monitor.py
│       ├── ca-health-check.py
│       └── vault-metrics-exporter.py
│
└── compliance/
    ├── audit-logs/
    │   ├── vault-audit.log
    │   ├── certificate-issuance.log
    │   ├── certificate-revocation.log
    │   └── ca-operations.log
    │
    ├── reports/
    │   ├── pki-inventory.json
    │   ├── compliance-dashboard.json
    │   └── security-posture-report.pdf
    │
    └── policies/
        ├── certificate-lifecycle-policy.yaml
        ├── key-management-policy.yaml
        └── ca-security-policy.yaml
```

## Certificate Profiles and Extended Key Usage

### 1. TLS Server Certificates
```yaml
tls_server_profile:
  extended_key_usage:
    - server_auth
  key_usage:
    - digital_signature
    - key_encipherment
  subject_alt_names:
    - DNS names
    - IP addresses
  validity: 90 days
  auto_rotation: true
```

### 2. TLS Client Certificates
```yaml
tls_client_profile:
  extended_key_usage:
    - client_auth
  key_usage:
    - digital_signature
    - key_encipherment
  validity: 365 days
  auto_rotation: false
```

### 3. Agent Identity Certificates (Special EKU)
```yaml
agent_identity_profile:
  extended_key_usage:
    - client_auth
    - 1.3.6.1.4.1.311.10.3.13  # Lifetime Signing
    - 1.2.840.113549.1.9.16.3.8  # Time Stamping
    - 1.3.6.1.5.5.7.3.17  # IPSec User
  key_usage:
    - digital_signature
    - key_encipherment
    - non_repudiation
  custom_extensions:
    agent_type: "{{ agent_name }}"
    framework_version: "{{ framework_version }}"
    capability_level: "{{ capability_level }}"
  validity: 30 days
  auto_rotation: true
```

### 4. Code Signing Certificates
```yaml
code_signing_profile:
  extended_key_usage:
    - code_signing
    - 1.3.6.1.4.1.311.10.3.13  # Lifetime Signing
  key_usage:
    - digital_signature
  validity: 365 days
  auto_rotation: false
  time_stamping_required: true
```

## HashiCorp Vault Configuration

### Vault Configuration File
```hcl
# vault-config.hcl
storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_cert_file = "/vault/certs/vault-server.crt"
  tls_key_file  = "/vault/certs/vault-server.key"
  tls_client_ca_file = "/vault/certs/vault-ca.crt"
  tls_require_and_verify_client_cert = true
}

api_addr = "https://vault:8200"
cluster_addr = "https://vault:8201"

ui = true
log_level = "INFO"

# Enable audit logging
audit "file" {
  file_path = "/vault/logs/vault-audit.log"
}

# PKI secrets engines
path "pki" {
  type = "pki"
}

path "pki_int" {
  type = "pki"
}
```

### Docker Compose for Vault PKI
```yaml
# vault-pki-compose.yml
version: '3.8'

services:
  vault:
    image: hashicorp/vault:latest
    container_name: cybersec-vault
    ports:
      - "8200:8200"
      - "8201:8201"
    volumes:
      - ./vault-pki/config/vault-config.hcl:/vault/config/vault.hcl:ro
      - vault_data:/vault/data
      - vault_logs:/vault/logs
      - ./vault-pki/service-certificates/tls/services/vault-server:/vault/certs:ro
    environment:
      - VAULT_ADDR=https://0.0.0.0:8200
      - VAULT_API_ADDR=https://vault:8200
      - VAULT_CLUSTER_ADDR=https://vault:8201
    command: vault server -config=/vault/config/vault.hcl
    cap_add:
      - IPC_LOCK
    networks:
      - cybersec-pki

  vault-init:
    image: hashicorp/vault:latest
    container_name: vault-init
    volumes:
      - ./vault-pki/automation/vault-scripts:/scripts:ro
      - vault_init_data:/vault-init
    environment:
      - VAULT_ADDR=https://vault:8200
      - VAULT_CACERT=/scripts/vault-ca.crt
    depends_on:
      - vault
    command: /scripts/setup-vault-pki.sh
    networks:
      - cybersec-pki

  # PKI Management Service
  pki-manager:
    image: cybersec-framework/pki-manager:latest
    container_name: pki-manager
    volumes:
      - ./vault-pki:/pki-config:ro
      - ./vault-pki/automation:/automation:ro
    environment:
      - VAULT_ADDR=https://vault:8200
      - VAULT_TOKEN_FILE=/pki-config/vault-token
    depends_on:
      - vault
      - vault-init
    networks:
      - cybersec-pki

  # Certificate Monitor
  cert-monitor:
    image: cybersec-framework/cert-monitor:latest
    container_name: cert-monitor
    volumes:
      - ./vault-pki/automation/monitoring:/monitoring:ro
      - ./vault-pki/compliance:/compliance
    environment:
      - VAULT_ADDR=https://vault:8200
      - MONITORING_INTERVAL=3600
      - ALERT_WEBHOOK_URL=${ALERT_WEBHOOK_URL}
    depends_on:
      - vault
    networks:
      - cybersec-pki

volumes:
  vault_data:
  vault_logs:
  vault_init_data:

networks:
  cybersec-pki:
    driver: bridge
    internal: true
```

## Vault PKI Setup Script

### Initial PKI Configuration
```bash
#!/bin/bash
# setup-vault-pki.sh

set -euo pipefail

# Wait for Vault to be ready
until vault status; do
  echo "Waiting for Vault to be ready..."
  sleep 5
done

# Initialize Vault if not already done
if ! vault status | grep -q "Initialized.*true"; then
  echo "Initializing Vault..."
  vault operator init -key-shares=5 -key-threshold=3 > /vault-init/init-keys.txt
  
  # Unseal Vault
  UNSEAL_KEYS=$(grep "Unseal Key" /vault-init/init-keys.txt | cut -d: -f2 | tr -d ' ')
  for key in $(echo "$UNSEAL_KEYS" | head -3); do
    vault operator unseal "$key"
  done
  
  # Get root token
  ROOT_TOKEN=$(grep "Initial Root Token" /vault-init/init-keys.txt | cut -d: -f2 | tr -d ' ')
  export VAULT_TOKEN="$ROOT_TOKEN"
else
  # Use existing root token
  export VAULT_TOKEN=$(cat /vault-init/root-token)
fi

# Enable PKI secrets engines
echo "Setting up PKI secrets engines..."

# 1. Enable TLS CA
vault secrets enable -path=tls-ca pki
vault secrets tune -max-lease-ttl=87600h tls-ca

# 2. Enable Auth CA  
vault secrets enable -path=auth-ca pki
vault secrets tune -max-lease-ttl=87600h auth-ca

# 3. Enable Code Signing CA
vault secrets enable -path=code-signing-ca pki
vault secrets tune -max-lease-ttl=43800h code-signing-ca

# 4. Enable Agent Attestation CA
vault secrets enable -path=agent-attestation-ca pki
vault secrets tune -max-lease-ttl=43800h agent-attestation-ca

# Generate intermediate CA certificates
echo "Generating intermediate CA certificates..."

# TLS Intermediate CA
vault write -field=csr tls-ca/intermediate/generate/internal \
  common_name="CyberSec Framework TLS Intermediate CA" \
  organization="CyberSec Framework" \
  ou="Infrastructure Security" \
  key_type="rsa" \
  key_bits="4096" \
  > /tmp/tls-intermediate.csr

# Sign with primary root CA (offline process - manual for now)
echo "TLS Intermediate CSR generated. Sign with Primary Root CA offline."

# Auth Intermediate CA
vault write -field=csr auth-ca/intermediate/generate/internal \
  common_name="CyberSec Framework Authentication Intermediate CA" \
  organization="CyberSec Framework" \
  ou="Identity Security" \
  key_type="rsa" \
  key_bits="4096" \
  > /tmp/auth-intermediate.csr

echo "Auth Intermediate CSR generated. Sign with Primary Root CA offline."

# Code Signing Intermediate CA
vault write -field=csr code-signing-ca/intermediate/generate/internal \
  common_name="CyberSec Framework Code Signing Intermediate CA" \
  organization="CyberSec Framework" \
  ou="Code Security" \
  key_type="rsa" \
  key_bits="4096" \
  > /tmp/code-signing-intermediate.csr

echo "Code Signing Intermediate CSR generated. Sign with Secondary Root CA offline."

# Agent Attestation Intermediate CA
vault write -field=csr agent-attestation-ca/intermediate/generate/internal \
  common_name="CyberSec Framework Agent Attestation Intermediate CA" \
  organization="CyberSec Framework" \
  ou="Agent Security" \
  key_type="rsa" \
  key_bits="4096" \
  > /tmp/agent-attestation-intermediate.csr

echo "Agent Attestation Intermediate CSR generated. Sign with Secondary Root CA offline."

echo "PKI setup completed. Intermediate CA CSRs ready for offline signing."
```

This enterprise PKI architecture provides:

1. **Dual Root CAs** for separation of concerns
2. **Proper certificate hierarchies** for different use cases
3. **Specific EKU configurations** for agents with custom extensions
4. **HashiCorp Vault integration** for automated certificate management
5. **Enterprise security controls** including audit logging and compliance monitoring
6. **Zero-downtime certificate rotation** capabilities
7. **Comprehensive monitoring** and alerting

The architecture follows industry best practices for high-security environments while providing the automation needed for your cybersecurity framework.
