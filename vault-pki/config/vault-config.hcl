# HashiCorp Vault Configuration for Enterprise PKI
# CyberSec Framework - Dual Root CA with Cross-Certification

# Backend storage configuration
storage "file" {
  path = "/vault/data"
}

# HTTPS API listener with mTLS
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/vault/certs/vault-server.crt"
  tls_key_file  = "/vault/certs/vault-server.key"
  tls_client_ca_file = "/vault/certs/vault-ca.crt"
  tls_require_and_verify_client_cert = false  # Set to true after initial setup
  tls_min_version = "tls12"
}

# Vault cluster configuration
api_addr = "https://vault:8200"
cluster_addr = "https://vault:8201"

# UI and logging
ui = true
log_level = "INFO"
log_format = "json"

# Performance and caching
default_lease_ttl = "768h"    # 32 days
max_lease_ttl = "8760h"       # 1 year

# Enable audit logging
audit "file" {
  file_path = "/vault/logs/vault-audit.log"
  format = "json"
}

# Enable syslog for additional logging
audit "syslog" {
  tag = "vault-pki"
}

# Enable performance and telemetry
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

# Seal configuration (auto-unseal with cloud KMS in production)
# For local development, using shamir sealing
seal "shamir" {
  # This will use the default Shamir seal
}

# PKI Performance tuning
raw_storage_endpoint = true
