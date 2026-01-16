# Vault Policy: Platform Admin
# Full access to all secrets

path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# PKI management
path "pki/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Database secrets engine
path "database/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Transit encryption
path "transit/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Auth methods
path "auth/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# System backend
path "sys/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
