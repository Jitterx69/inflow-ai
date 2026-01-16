# Traffic Surge Handling

> Procedures for handling unexpected traffic spikes.

## Detection

Traffic surge detected when:
- Request rate > 2x normal baseline
- HPA already at max replicas
- Latency increasing

---

## Immediate Actions

### 1. Scale Critical Services

```bash
# Scale inference (most resource-intensive)
kubectl scale deployment/inference-service -n inflow-prod --replicas=10

# Scale decision engine
kubectl scale deployment/decision-engine -n inflow-prod --replicas=8

# Scale feature service
kubectl scale deployment/feature-service -n inflow-prod --replicas=6
```

### 2. Enable Aggressive Rate Limiting

```bash
# Apply stricter rate limits
kubectl apply -f infra/kubernetes/components/scaling/rate-limits-strict.yaml

# Or update configmap
kubectl patch configmap rate-limit-config -n inflow-prod \
  --type='json' \
  -p='[{"op": "replace", "path": "/data/requests_per_second", "value": "100"}]'
```

### 3. Disable Non-Critical Features

```bash
# Disable LLM (reduces load significantly)
kubectl set env deployment/llm-service -n inflow-prod LLM_ENABLED=false

# Disable detailed explanations
kubectl set env deployment/inference-service -n inflow-prod EXPLAIN_ENABLED=false
```

---

## HPA Limits

| Service | Normal Max | Surge Max |
|---------|------------|-----------|
| ingestion | 10 | 20 |
| feature-service | 10 | 15 |
| inference-service | 15 | 30 |
| decision-engine | 10 | 15 |

### Temporarily Increase HPA Max

```bash
kubectl patch hpa inference-service-hpa -n inflow-prod \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/maxReplicas", "value": 30}]'
```

---

## If Scaling Isn't Enough

### Graceful Degradation

```bash
# Enable degraded mode
kubectl set env deployment/decision-engine -n inflow-prod DEGRADED_MODE=true
```

In degraded mode:
- Only critical requests processed
- Complex decisions queued
- Simple threshold-based responses

### Queue Backpressure

```bash
# Reduce Kafka consumer concurrency
kubectl set env deployment/ingestion -n inflow-prod CONSUMER_CONCURRENCY=1

# Add lag tolerance
kubectl set env deployment/ingestion -n inflow-prod MAX_LAG_TOLERANCE=10000
```

---

## Post-Surge

After traffic normalizes:

1. **Wait 15 min** for stability
2. **Scale down** gradually:
   ```bash
   kubectl scale deployment/inference-service -n inflow-prod --replicas=5
   ```
3. **Re-enable features**:
   ```bash
   kubectl set env deployment/llm-service -n inflow-prod LLM_ENABLED=true
   ```
4. **Reset HPA limits** to normal
5. **Analyze** traffic patterns for capacity planning

---

## Metrics to Watch

| Metric | Threshold |
|--------|-----------|
| Request rate | vs baseline |
| P99 latency | < 500ms |
| Error rate | < 1% |
| CPU usage | < 80% |
| HPA replicas | vs max |
