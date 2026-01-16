# Vault Policy: Production
# Strict access for production secrets

# Production secrets - read only for services
path "secret/data/prod/*" {
  capabilities = ["read"]
}

path "secret/metadata/prod/*" {
  capabilities = ["read", "list"]
}

# Database credentials - dynamic
path "database/creds/prod-*" {
  capabilities = ["read"]
}

# PKI for mTLS
path "pki/issue/prod-*" {
  capabilities = ["create", "update"]
}

# Transit encryption for sensitive data
path "transit/encrypt/prod-*" {
  capabilities = ["create", "update"]
}

path "transit/decrypt/prod-*" {
  capabilities = ["create", "update"]
}

# Deny access to non-prod paths
path "secret/data/dev/*" {
  capabilities = ["deny"]
}

path "secret/data/staging/*" {
  capabilities = ["deny"]
}

# No policy management in prod
path "sys/policies/*" {
  capabilities = ["deny"]
}

path "auth/*" {
  capabilities = ["deny"]
}
