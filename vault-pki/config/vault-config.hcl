# HashiCorp Vault Configuration for Enterprise PKI
# CyberSec Framework - Dual Root CA with Cross-Certification

# Backend storage configuration
storage "file" {
  path = "/vault/data"
}

# HTTP API listener for initial setup (switch to HTTPS in production)
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_disable   = true  # Disable TLS for initial setup
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
