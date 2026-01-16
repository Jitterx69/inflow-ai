# Local Development Guide

> One command to run the entire stack.

## Prerequisites

- Docker Desktop (v24+)
- Docker Compose (v2+)
- Python 3.11+ (for running scripts outside containers)
- Git

## Quick Start

```bash
# Clone and enter the repo
git clone https://github.com/Jitterx69/inflow-ai.git
cd inflow-ai

# Start all services
docker-compose -f docker-compose.dev.yml up --build

# Or run in background
docker-compose -f docker-compose.dev.yml up --build -d
```

## Service Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| Ingestion | http://localhost:8000 | Event ingestion |
| Inference | http://localhost:8001 | ML predictions |
| Features | http://localhost:8002 | Feature lookup |
| Decision | http://localhost:8003 | Decision engine |
| Redpanda Console | http://localhost:9644 | Kafka management |

## Health Checks

```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## Testing the Flow

### 1. Get Features

```bash
curl http://localhost:8002/v1/features/ACC001 | jq
```

### 2. Run Inference

```bash
curl -X POST http://localhost:8001/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-001",
    "features": {
      "account_id": "ACC001",
      "days_past_due": 45,
      "outstanding_balance": 1250.00,
      "payment_history_score": 0.65,
      "contact_attempts": 3,
      "last_payment_days_ago": 60,
      "account_age_months": 24
    }
  }' | jq
```

### 3. Get Decision

```bash
curl -X POST http://localhost:8003/v1/decide \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-001",
    "account_id": "ACC001",
    "prediction": {"label": "escalate", "confidence": 0.85},
    "features": {
      "account_id": "ACC001",
      "days_past_due": 45,
      "outstanding_balance": 1250.00,
      "payment_history_score": 0.65,
      "contact_attempts": 3,
      "last_payment_days_ago": 60,
      "account_age_months": 24
    }
  }' | jq
```

## Running ML Training

```bash
# Install dependencies
pip install -r ml/models/baseline/requirements.txt

# Train model
python ml/models/baseline/train.py

# Evaluate
python ml/models/baseline/eval.py

# Generate SHAP analysis
python ml/explainability/shap_summary.py
```

## Stopping Services

```bash
# Stop all
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

## Rebuilding After Changes

```bash
# Rebuild specific service
docker-compose -f docker-compose.dev.yml up --build ingestion

# Rebuild all
docker-compose -f docker-compose.dev.yml up --build
```

## Viewing Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f inference-service
```
