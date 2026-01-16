# Keycloak — Authentication & Authorization

> **Status**: P0 Skeleton — Intent Documentation Only

## Purpose

Keycloak provides:
- **OIDC** (OpenID Connect) for authentication
- **RBAC** (Role-Based Access Control) for authorization
- **SSO** (Single Sign-On) across all services

## Auth Model (Planned)

### Realms
| Realm | Purpose |
|-------|---------|
| `inflow` | Main application realm |
| `internal` | Platform/admin realm |

### Roles (Planned)
| Role | Description |
|------|-------------|
| `ml-engineer` | Access to ML pipelines and model registry |
| `backend-dev` | Access to services and APIs |
| `platform-admin` | Full infra access |
| `viewer` | Read-only access |

### Clients (Planned)
| Client | Type | Purpose |
|--------|------|---------|
| `inflow-api` | Confidential | Backend services |
| `inflow-ml` | Confidential | ML platform |
| `inflow-ui` | Public | Frontend application |

## Integration Points

- **Kubernetes**: OIDC authentication for kubectl
- **Vault**: Keycloak as identity provider
- **Grafana**: SSO via Keycloak
- **Airflow**: Role-based DAG access

## Next Steps (P1)

1. Deploy Keycloak to `inflow-platform` namespace
2. Configure realm and clients
3. Integrate with Vault for secret injection
4. Set up federation with corporate IdP (if applicable)

---

> ⚠️ **DO NOT** configure or deploy until P1. This is documentation only.
