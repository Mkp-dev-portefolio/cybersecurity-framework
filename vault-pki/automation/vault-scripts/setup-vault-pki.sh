#!/bin/bash
# Enterprise PKI Setup Script for HashiCorp Vault
# CyberSec Framework - Dual Root CA with Cross-Certification

set -euo pipefail

# Configuration
VAULT_ADDR="${VAULT_ADDR:-https://vault:8200}"
VAULT_INIT_FILE="/vault-init/init-keys.txt"
VAULT_TOKEN_FILE="/vault-init/vault-token"
LOG_FILE="/vault/logs/pki-setup.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

log "Starting Enterprise PKI setup for CyberSec Framework"

# Wait for Vault to be ready
log "Waiting for Vault to be ready..."
until vault status >/dev/null 2>&1; do
    log "Vault not ready, waiting 5 seconds..."
    sleep 5
done

log "Vault is ready, proceeding with setup"

# Initialize Vault if not already done
if ! vault status | grep -q "Initialized.*true"; then
    log "Initializing Vault with 5 key shares, 3 key threshold"
    vault operator init \
        -key-shares=5 \
        -key-threshold=3 \
        -format=json > "$VAULT_INIT_FILE" || error_exit "Failed to initialize Vault"
    
    # Extract unseal keys and root token
    UNSEAL_KEYS=$(jq -r '.unseal_keys_b64[]' "$VAULT_INIT_FILE")
    ROOT_TOKEN=$(jq -r '.root_token' "$VAULT_INIT_FILE")
    
    # Unseal Vault
    log "Unsealing Vault..."
    counter=0
    for key in $UNSEAL_KEYS; do
        if [ $counter -lt 3 ]; then
            vault operator unseal "$key" || error_exit "Failed to unseal with key $((counter+1))"
            counter=$((counter+1))
        fi
    done
    
    # Save root token
    echo "$ROOT_TOKEN" > "$VAULT_TOKEN_FILE"
    chmod 600 "$VAULT_TOKEN_FILE"
    
    export VAULT_TOKEN="$ROOT_TOKEN"
    log "Vault initialized and unsealed successfully"
else
    log "Vault already initialized, loading existing token"
    if [ -f "$VAULT_TOKEN_FILE" ]; then
        export VAULT_TOKEN=$(cat "$VAULT_TOKEN_FILE")
    else
        error_exit "Vault is initialized but no token file found"
    fi
fi

# Enable audit logging if not already enabled
log "Configuring audit logging..."
if ! vault audit list | grep -q "file/"; then
    vault audit enable file file_path=/vault/logs/vault-audit.log || log "Warning: Could not enable file audit"
fi

# Enable PKI secrets engines
log "Setting up PKI secrets engines..."

# 1. TLS Intermediate CA
log "Enabling TLS CA at path: tls-ca"
if ! vault secrets list | grep -q "tls-ca/"; then
    vault secrets enable -path=tls-ca pki || error_exit "Failed to enable TLS CA"
    vault secrets tune -max-lease-ttl=87600h tls-ca || error_exit "Failed to tune TLS CA"
fi

# 2. Authentication Intermediate CA
log "Enabling Auth CA at path: auth-ca"
if ! vault secrets list | grep -q "auth-ca/"; then
    vault secrets enable -path=auth-ca pki || error_exit "Failed to enable Auth CA"
    vault secrets tune -max-lease-ttl=87600h auth-ca || error_exit "Failed to tune Auth CA"
fi

# 3. Code Signing Intermediate CA
log "Enabling Code Signing CA at path: code-signing-ca"
if ! vault secrets list | grep -q "code-signing-ca/"; then
    vault secrets enable -path=code-signing-ca pki || error_exit "Failed to enable Code Signing CA"
    vault secrets tune -max-lease-ttl=43800h code-signing-ca || error_exit "Failed to tune Code Signing CA"
fi

# 4. Agent Attestation Intermediate CA
log "Enabling Agent Attestation CA at path: agent-attestation-ca"
if ! vault secrets list | grep -q "agent-attestation-ca/"; then
    vault secrets enable -path=agent-attestation-ca pki || error_exit "Failed to enable Agent Attestation CA"
    vault secrets tune -max-lease-ttl=43800h agent-attestation-ca || error_exit "Failed to tune Agent Attestation CA"
fi

# Generate intermediate CA CSRs
log "Generating intermediate CA certificate signing requests..."

# TLS Intermediate CA CSR
log "Generating TLS Intermediate CA CSR"
vault write -field=csr tls-ca/intermediate/generate/internal \
    common_name="CyberSec Framework TLS Intermediate CA" \
    organization="CyberSec Framework" \
    ou="Infrastructure Security" \
    country="US" \
    locality="San Francisco" \
    province="CA" \
    key_type="rsa" \
    key_bits="4096" \
    exclude_cn_from_sans=true \
    > /tmp/tls-intermediate.csr || error_exit "Failed to generate TLS intermediate CSR"

# Auth Intermediate CA CSR
log "Generating Auth Intermediate CA CSR"
vault write -field=csr auth-ca/intermediate/generate/internal \
    common_name="CyberSec Framework Authentication Intermediate CA" \
    organization="CyberSec Framework" \
    ou="Identity Security" \
    country="US" \
    locality="San Francisco" \
    province="CA" \
    key_type="rsa" \
    key_bits="4096" \
    exclude_cn_from_sans=true \
    > /tmp/auth-intermediate.csr || error_exit "Failed to generate Auth intermediate CSR"

# Code Signing Intermediate CA CSR
log "Generating Code Signing Intermediate CA CSR"
vault write -field=csr code-signing-ca/intermediate/generate/internal \
    common_name="CyberSec Framework Code Signing Intermediate CA" \
    organization="CyberSec Framework" \
    ou="Code Security" \
    country="US" \
    locality="San Francisco" \
    province="CA" \
    key_type="rsa" \
    key_bits="4096" \
    exclude_cn_from_sans=true \
    > /tmp/code-signing-intermediate.csr || error_exit "Failed to generate Code Signing intermediate CSR"

# Agent Attestation Intermediate CA CSR
log "Generating Agent Attestation Intermediate CA CSR"
vault write -field=csr agent-attestation-ca/intermediate/generate/internal \
    common_name="CyberSec Framework Agent Attestation Intermediate CA" \
    organization="CyberSec Framework" \
    ou="Agent Security" \
    country="US" \
    locality="San Francisco" \
    province="CA" \
    key_type="rsa" \
    key_bits="4096" \
    exclude_cn_from_sans=true \
    > /tmp/agent-attestation-intermediate.csr || error_exit "Failed to generate Agent Attestation intermediate CSR"

# Copy CSRs to permanent location
log "Copying CSRs to permanent location"
mkdir -p /vault-init/intermediate-csrs
cp /tmp/*-intermediate.csr /vault-init/intermediate-csrs/

log "✅ PKI setup phase 1 completed successfully!"
log "📋 Next steps:"
log "   1. Sign intermediate CA CSRs with offline root CAs"
log "   2. Install signed intermediate certificates"
log "   3. Configure certificate roles and policies"
log "   4. Set up automated certificate issuance"

log "📁 Files created:"
log "   - Vault initialization: $VAULT_INIT_FILE"
log "   - Root token: $VAULT_TOKEN_FILE"
log "   - TLS Intermediate CSR: /vault-init/intermediate-csrs/tls-intermediate.csr"
log "   - Auth Intermediate CSR: /vault-init/intermediate-csrs/auth-intermediate.csr"
log "   - Code Signing Intermediate CSR: /vault-init/intermediate-csrs/code-signing-intermediate.csr"
log "   - Agent Attestation Intermediate CSR: /vault-init/intermediate-csrs/agent-attestation-intermediate.csr"

log "Enterprise PKI setup completed! 🚀"
