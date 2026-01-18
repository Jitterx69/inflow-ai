"""
Audit Logger
Provides immutable audit trail for all model decisions.
Every prediction is reconstructible.
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AuditRecord:
    """Immutable audit record for a decision."""
    
    # Identifiers
    audit_id: str
    request_id: str
    account_id: str
    timestamp: str
    
    # Model info
    model_name: str
    model_version: str
    model_hash: str
    
    # Feature snapshot
    feature_snapshot_id: str
    feature_version: str
    
    # Prediction
    prediction: str
    confidence: float
    raw_scores: dict
    
    # Explanation
    explanation_pointer: str  # Reference to stored explanation
    shap_summary: dict
    
    # Decision
    decision_action: str
    decision_reason: str
    human_override: bool
    
    # Metadata
    service_version: str
    environment: str
    
    def compute_hash(self) -> str:
        """Compute hash for integrity verification."""
        content = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class AuditLogger:
    """
    Audit logger for model decisions.
    Ensures every decision can be reconstructed.
    """
    
    def __init__(self, storage_backend: str = "local"):
        self.storage_backend = storage_backend
        self.records: list[AuditRecord] = []  # In-memory for demo
        logger.info(f"AuditLogger initialized with backend: {storage_backend}")
    
    def log_prediction(
        self,
        request_id: str,
        account_id: str,
        model_name: str,
        model_version: str,
        model_hash: str,
        feature_snapshot_id: str,
        feature_version: str,
        prediction: str,
        confidence: float,
        raw_scores: dict,
        shap_values: dict,
        decision_action: str,
        decision_reason: str,
        human_override: bool = False
    ) -> str:
        """
        Log a prediction for audit purposes.
        
        Returns:
            Audit ID for reference
        """
        timestamp = datetime.utcnow().isoformat()
        audit_id = f"audit_{request_id}_{timestamp.replace(':', '').replace('-', '')}"
        
        record = AuditRecord(
            audit_id=audit_id,
            request_id=request_id,
            account_id=account_id,
            timestamp=timestamp,
            model_name=model_name,
            model_version=model_version,
            model_hash=model_hash,
            feature_snapshot_id=feature_snapshot_id,
            feature_version=feature_version,
            prediction=prediction,
            confidence=confidence,
            raw_scores=raw_scores,
            explanation_pointer=f"s3://audit/explanations/{audit_id}.json",
            shap_summary=shap_values,
            decision_action=decision_action,
            decision_reason=decision_reason,
            human_override=human_override,
            service_version=os.getenv("SERVICE_VERSION", "0.1.0"),
            environment=os.getenv("ENVIRONMENT", "dev")
        )
        
        # Store record
        self._store_record(record)
        
        # Log for observability
        logger.info(
            f"Audit logged: {audit_id} | "
            f"model={model_name}:{model_version} | "
            f"prediction={prediction} | "
            f"confidence={confidence:.2f}"
        )
        
        return audit_id
    
    def _store_record(self, record: AuditRecord):
        """Store audit record to backend."""
        # In production: write to immutable storage (S3, BigQuery, etc.)
        self.records.append(record)
        
        # Verify integrity
        record_hash = record.compute_hash()
        logger.debug(f"Record hash: {record_hash}")
    
    def get_record(self, audit_id: str) -> Optional[AuditRecord]:
        """Retrieve audit record by ID."""
        for record in self.records:
            if record.audit_id == audit_id:
                return record
        return None
    
    def reconstruct_decision(self, audit_id: str) -> dict:
        """
        Reconstruct a decision from audit trail.
        Answers: "Why did the system do this?"
        """
        record = self.get_record(audit_id)
        if not record:
            return {"error": f"Audit record not found: {audit_id}"}
        
        return {
            "audit_id": record.audit_id,
            "question": "Why did the system make this decision?",
            "answer": {
                "when": record.timestamp,
                "what_model": f"{record.model_name}:{record.model_version}",
                "model_integrity": record.model_hash[:16] + "...",
                "input_features": record.feature_snapshot_id,
                "prediction": record.prediction,
                "confidence": record.confidence,
                "decision": record.decision_action,
                "reason": record.decision_reason,
                "top_factors": list(record.shap_summary.keys())[:3],
                "human_involved": record.human_override
            },
            "reconstructible": True
        }
    
    def query_by_account(self, account_id: str, limit: int = 10) -> list[dict]:
        """Query audit records for an account."""
        matches = [r for r in self.records if r.account_id == account_id]
        return [asdict(r) for r in matches[:limit]]


# Global audit logger instance
audit_logger = AuditLogger()


def log_decision(
    request_id: str,
    account_id: str,
    model_info: dict,
    features: dict,
    prediction: dict,
    decision: dict
) -> str:
    """Convenience function for logging decisions."""
    return audit_logger.log_prediction(
        request_id=request_id,
        account_id=account_id,
        model_name=model_info.get("name", "unknown"),
        model_version=model_info.get("version", "unknown"),
        model_hash=model_info.get("hash", "unknown"),
        feature_snapshot_id=features.get("snapshot_id", "unknown"),
        feature_version=features.get("version", "v1"),
        prediction=prediction.get("class", "unknown"),
        confidence=prediction.get("confidence", 0.0),
        raw_scores=prediction.get("scores", {}),
        shap_values=prediction.get("shap", {}),
        decision_action=decision.get("action", "unknown"),
        decision_reason=decision.get("reason", ""),
        human_override=decision.get("human_override", False)
    )
