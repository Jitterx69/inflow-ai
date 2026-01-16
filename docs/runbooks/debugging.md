# Debugging Guide

> Common failures and how to fix them.

## Service Won't Start

### Symptom: Container exits immediately

**Check logs:**
```bash
docker-compose -f docker-compose.dev.yml logs <service-name>
```

**Common causes:**

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError` | Rebuild: `docker-compose up --build` |
| `Address already in use` | Kill process on port: `lsof -ti:8000 | xargs kill` |
| `Permission denied` | Check file permissions |

### Symptom: Health check failing

```bash
# Check if service is responding
curl -v http://localhost:8000/health

# Check container status
docker ps -a
```

## Redpanda/Kafka Issues

### Symptom: "Connection refused" to Kafka

**Verify Redpanda is running:**
```bash
docker-compose -f docker-compose.dev.yml ps redpanda
```

**Check Redpanda logs:**
```bash
docker-compose -f docker-compose.dev.yml logs redpanda
```

**Test connectivity:**
```bash
docker exec inflow-redpanda rpk cluster info
```

### Symptom: Topics not created

```bash
# List topics
docker exec inflow-redpanda rpk topic list

# Create topic manually
docker exec inflow-redpanda rpk topic create inflow-events
```

## Model Loading Issues

### Symptom: "Model not loaded" error

**Check if artifacts exist:**
```bash
ls -la ml/models/baseline/artifacts/
```

**Run training if missing:**
```bash
python ml/models/baseline/train.py
```

### Symptom: Wrong predictions

1. Check model version in health endpoint
2. Verify feature values are in expected ranges
3. Run evaluation: `python ml/models/baseline/eval.py`

## Network Issues

### Symptom: Services can't communicate

**Check network:**
```bash
docker network ls
docker network inspect inflow-network
```

**Verify DNS resolution inside container:**
```bash
docker exec inflow-ingestion ping feature-service
```

## Memory Issues

### Symptom: Container OOM killed

**Check memory usage:**
```bash
docker stats
```

**Increase Docker memory** in Docker Desktop settings.

## Database/Feature Store Issues

### Symptom: "Feature store not connected"

Currently using mock data. Real feature store integration is in P2+.

**Workaround:** Use mock accounts (ACC001, ACC002, ACC003).

## CI Pipeline Failures

### Symptom: Lint errors

```bash
# Run locally
pip install ruff yamllint
ruff check .
yamllint .
```

### Symptom: Tests failing

```bash
# Run tests locally
pip install pytest
pytest services/*/test_*.py
```

## Getting Help

1. Check service logs first
2. Verify all containers are running: `docker ps`
3. Check health endpoints
4. Review recent commits for breaking changes
5. Ask in team channel with:
   - Error message
   - Steps to reproduce
   - Relevant logs
