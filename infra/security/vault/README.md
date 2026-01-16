# HashiCorp Vault — Secret Management Strategy

> **Status**: P0 Skeleton — Intent Documentation Only

## Purpose

Vault provides:
- **Secret Storage**: Encrypted at rest and in transit
- **Dynamic Secrets**: Short-lived credentials for databases, cloud providers
- **PKI**: Certificate management for mTLS
- **Encryption as a Service**: Transit secrets engine

## Secret Strategy (Planned)

### Secret Engines
| Engine | Path | Purpose |
|--------|------|---------|
| KV v2 | `secret/` | Static secrets (API keys, configs) |
| Database | `database/` | Dynamic DB credentials |
| PKI | `pki/` | TLS certificates |
| Transit | `transit/` | Encryption keys |

### Namespace Structure
```
vault/
├── inflow-ml/
│   ├── model-registry-creds
│   ├── training-api-keys
│   └── inference-secrets
├── inflow-services/
│   ├── database-creds
│   ├── kafka-creds
│   └── external-api-keys
└── inflow-platform/
    ├── kubernetes-auth
    ├── monitoring-creds
    └── backup-keys
```

### Access Policies (Planned)
| Policy | Access |
|--------|--------|
| `ml-read` | Read ML secrets only |
| `services-read` | Read service secrets only |
| `platform-admin` | Full access |

## Integration Points

- **Kubernetes**: Vault Agent Injector for pod secrets
- **CI/CD**: GitHub Actions OIDC auth
- **Keycloak**: Vault as secret backend

## Next Steps (P1)

1. Deploy Vault in HA mode to `inflow-platform`
2. Configure Kubernetes auth method
3. Set up secret engines
4. Integrate with GitHub Actions

---

> ⚠️ **DO NOT** store any real secrets until P1. This is documentation only.
