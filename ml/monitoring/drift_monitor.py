"""
ML Monitoring Module
Tracks data drift and model performance decay.
"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataDriftMonitor:
    """
    Monitors feature distribution drift using statistical tests.
    """
    
    def __init__(self, reference_stats: Optional[dict] = None):
        self.reference_stats = reference_stats or {}
        self.alerts = []
    
    def compute_stats(self, data: np.ndarray) -> dict:
        """Compute distribution statistics."""
        return {
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "median": float(np.median(data)),
            "p25": float(np.percentile(data, 25)),
            "p75": float(np.percentile(data, 75)),
        }
    
    def set_reference(self, feature_name: str, data: np.ndarray):
        """Set reference distribution for a feature."""
        self.reference_stats[feature_name] = self.compute_stats(data)
        logger.info(f"Set reference for {feature_name}")
    
    def check_drift(
        self,
        feature_name: str,
        current_data: np.ndarray,
        threshold: float = 0.1
    ) -> dict:
        """
        Check for drift using Population Stability Index (PSI).
        
        Args:
            feature_name: Feature to check
            current_data: Current data distribution
            threshold: PSI threshold (>0.1 = drift, >0.2 = significant)
            
        Returns:
            Drift report dict
        """
        if feature_name not in self.reference_stats:
            return {"error": f"No reference for {feature_name}"}
        
        ref = self.reference_stats[feature_name]
        current = self.compute_stats(current_data)
        
        # Simple mean shift detection
        mean_shift = abs(current["mean"] - ref["mean"]) / (ref["std"] + 1e-6)
        std_ratio = current["std"] / (ref["std"] + 1e-6)
        
        drift_detected = mean_shift > 2.0 or std_ratio > 2.0 or std_ratio < 0.5
        
        report = {
            "feature": feature_name,
            "timestamp": datetime.utcnow().isoformat(),
            "reference": ref,
            "current": current,
            "mean_shift_zscore": float(mean_shift),
            "std_ratio": float(std_ratio),
            "drift_detected": drift_detected,
            "severity": "high" if mean_shift > 3.0 else "medium" if drift_detected else "low"
        }
        
        if drift_detected:
            self.alerts.append(report)
            logger.warning(f"Drift detected for {feature_name}: shift={mean_shift:.2f}")
        
        return report


class PerformanceMonitor:
    """
    Monitors model performance metrics over time.
    """
    
    def __init__(self):
        self.metrics_history = []
        self.decay_threshold = 0.05  # 5% performance drop
    
    def log_metrics(self, metrics: dict):
        """Log metrics snapshot."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            **metrics
        }
        self.metrics_history.append(entry)
    
    def check_decay(self, baseline_metric: str = "f1_weighted") -> dict:
        """
        Check for performance decay vs baseline.
        
        Returns:
            Decay report dict
        """
        if len(self.metrics_history) < 2:
            return {"error": "Insufficient history"}
        
        baseline = self.metrics_history[0].get(baseline_metric, 0)
        current = self.metrics_history[-1].get(baseline_metric, 0)
        
        decay = (baseline - current) / (baseline + 1e-6)
        decay_detected = decay > self.decay_threshold
        
        return {
            "metric": baseline_metric,
            "baseline": baseline,
            "current": current,
            "decay_percent": float(decay * 100),
            "decay_detected": decay_detected,
            "action": "retrain" if decay_detected else "none"
        }


# Alert thresholds
ALERT_THRESHOLDS = {
    "drift_psi": 0.2,
    "performance_decay": 0.05,
    "latency_p99_ms": 100,
    "error_rate": 0.01,
    "confidence_low_rate": 0.1,
}
