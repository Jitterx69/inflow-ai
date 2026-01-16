# LLM Disable Switch

> Emergency procedure to disable LLM functionality.

## When to Use

- LLM provider outage lasting > 10 min
- Cost runaway (daily budget exceeded)
- Quality degradation (hallucinations detected)
- Security concern

---

## Quick Disable (Immediate)

### Option 1: Environment Variable

```bash
# Disable LLM for the service
kubectl set env deployment/llm-service -n inflow-prod LLM_ENABLED=false

# Verify
kubectl rollout status deployment/llm-service -n inflow-prod
```

### Option 2: Scale to Zero

```bash
# Kill all LLM pods
kubectl scale deployment/llm-service -n inflow-prod --replicas=0

# Verify
kubectl get pods -n inflow-prod -l app=llm-service
```

### Option 3: Feature Flag (if implemented)

```bash
# Toggle feature flag
curl -X POST https://api.inflow.ai/admin/features \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"feature": "llm_enabled", "value": false}'
```

---

## What Happens When Disabled

When LLM is disabled:

1. **Summarization** → Returns "Summary unavailable"
2. **Explanation** → Returns standard template
3. **Suggestions** → Falls back to rule-based engine

**No impact on:**
- ML predictions (XGBoost)
- Decision engine (rule-based)
- Feature service
- Core business logic

---

## Verification

```bash
# Test fallback is working
curl https://api.inflow.ai/v1/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"use_case": "summarization", "context": "test"}'

# Expected response
{
  "is_fallback": true,
  "response": "Summary unavailable. Please refer to the raw data."
}
```

---

## Re-enable

```bash
# Re-enable via env
kubectl set env deployment/llm-service -n inflow-prod LLM_ENABLED=true

# Or scale back up
kubectl scale deployment/llm-service -n inflow-prod --replicas=2

# Verify health
curl https://llm-service.inflow-prod/health
```

---

## Monitoring

After disabling, monitor:

| Metric | Expected |
|--------|----------|
| `llm_fallback_rate` | 100% |
| `llm_requests_total` | Drops to 0 |
| `llm_tokens_used` | Stops increasing |
| API error rate | Should decrease |
