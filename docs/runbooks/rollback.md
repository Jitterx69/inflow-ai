# Rollback Procedures

> Emergency rollback for services and models.

## Quick Reference

| Component | Rollback Command |
|-----------|------------------|
| Services | `kubectl rollout undo deployment/<name>` |
| Model | `mlflow models update --stage Archived` |
| Infra | `kubectl apply -k infra/kubernetes/environments/<prev>` |

---

## Service Rollback

### Automatic Rollback Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Error rate | > 5% for 5 min | Alert + auto-rollback |
| Latency | p99 > 2x baseline for 10 min | Alert |
| Health check | 3 consecutive failures | Restart pod |

### Manual Service Rollback

```bash
# View rollout history
kubectl rollout history deployment/inference-service -n inflow-staging

# Rollback to previous
kubectl rollout undo deployment/inference-service -n inflow-staging

# Rollback to specific revision
kubectl rollout undo deployment/inference-service -n inflow-staging --to-revision=2

# Verify
kubectl rollout status deployment/inference-service -n inflow-staging
```

---

## Model Rollback

### MLflow Model Rollback

```bash
# List versions
mlflow models list --name inflow-baseline

# Archive current production
mlflow models update --name inflow-baseline --version 5 --stage Archived

# Promote previous to production
mlflow models update --name inflow-baseline --version 4 --stage Production
```

### KServe Model Rollback

```bash
# Update InferenceService to previous version
kubectl patch inferenceservice inflow-baseline -n inflow-staging \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/predictor/xgboost/storageUri", "value": "s3://models/baseline/v4"}]'
```

---

## Full Environment Rollback

```bash
# Checkout previous version
git checkout v1.x.x

# Apply previous manifests
kubectl apply -k infra/kubernetes/environments/staging
```

---

## Rollback Checklist

1. [ ] Identify failing component
2. [ ] Trigger rollback (auto or manual)
3. [ ] Verify rollback successful
4. [ ] Notify team in #incidents
5. [ ] Create incident report

---

## Post-Rollback

After stabilizing:

1. Create incident report
2. Root cause analysis within 48h
3. Create fix PR
4. Re-deploy through normal flow
