# Vault Policy: Services Team
# Read access to service secrets only

path "secret/data/services/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/services/*" {
  capabilities = ["read", "list"]
}

# Database credentials
path "database/creds/services-*" {
  capabilities = ["read"]
}

# Kafka credentials
path "secret/data/kafka/*" {
  capabilities = ["read"]
}

# Deny access to other paths
path "secret/data/ml/*" {
  capabilities = ["deny"]
}

path "secret/data/platform/*" {
  capabilities = ["deny"]
}
