# Vault Policy: ML Team
# Read access to ML secrets only

path "secret/data/ml/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/ml/*" {
  capabilities = ["read", "list"]
}

# Model registry credentials
path "secret/data/mlflow/*" {
  capabilities = ["read"]
}

# Feature store credentials
path "secret/data/feast/*" {
  capabilities = ["read"]
}

# Deny access to other paths
path "secret/data/services/*" {
  capabilities = ["deny"]
}

path "secret/data/platform/*" {
  capabilities = ["deny"]
}
