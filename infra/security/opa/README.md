# Open Policy Agent (OPA) — Policy-as-Code

> **Status**: P0 Skeleton — Intent Documentation Only

## Purpose

OPA provides:
- **Admission Control**: Validate Kubernetes resources before deployment
- **Authorization**: Fine-grained access decisions
- **Compliance**: Enforce organizational policies

## Policy Intent (Planned)

### Kubernetes Admission Policies
| Policy | Description |
|--------|-------------|
| `require-labels` | All resources must have `team` and `environment` labels |
| `deny-privileged` | No privileged containers allowed |
| `require-resource-limits` | All pods must specify CPU/memory limits |
| `deny-latest-tag` | No `latest` image tags in production |
| `require-readonly-root` | Root filesystem must be read-only |

### API Authorization Policies
| Policy | Description |
|--------|-------------|
| `ml-data-access` | ML team can only access training data |
| `service-mesh-auth` | mTLS required for inter-service communication |

### Compliance Policies
| Policy | Standard |
|--------|----------|
| `pci-dss` | Payment data isolation |
| `gdpr` | Data residency enforcement |

## Policy Structure (Planned)
```
infra/security/opa/
├── policies/
│   ├── kubernetes/
│   │   ├── require-labels.rego
│   │   ├── deny-privileged.rego
│   │   └── require-limits.rego
│   └── api/
│       └── authorization.rego
└── tests/
    └── kubernetes/
        └── require-labels_test.rego
```

## Integration Points

- **Gatekeeper**: OPA for Kubernetes admission control
- **Envoy**: External authorization filter
- **CI/CD**: Policy validation in pipelines

## Next Steps (P1)

1. Deploy Gatekeeper to cluster
2. Implement core admission policies
3. Set up policy testing in CI
4. Integrate with service mesh

---

> ⚠️ **DO NOT** deploy policies until P1. This is documentation only.
