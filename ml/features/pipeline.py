"""
Offline Feature Pipeline
Generates feature vectors from raw data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    Offline feature engineering pipeline.
    Transforms raw account data into ML-ready feature vectors.
    """
    
    FEATURE_SCHEMA = {
        'days_past_due': int,
        'outstanding_balance': float,
        'payment_history_score': float,
        'contact_attempts': int,
        'last_payment_days_ago': int,
        'account_age_months': int,
    }
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Initialize pipeline.
        
        Args:
            reference_date: Date to compute features relative to. Defaults to today.
        """
        self.reference_date = reference_date or datetime.utcnow()
    
    def compute_days_past_due(self, due_date: datetime) -> int:
        """Compute days since payment was due."""
        if due_date >= self.reference_date:
            return 0
        return (self.reference_date - due_date).days
    
    def compute_payment_history_score(self, payments: list[dict]) -> float:
        """
        Compute payment reliability score (0-1).
        
        Args:
            payments: List of payment records with 'on_time' boolean
        """
        if not payments:
            return 0.5  # Default for new accounts
        
        on_time_count = sum(1 for p in payments if p.get('on_time', False))
        return on_time_count / len(payments)
    
    def compute_last_payment_days(self, last_payment_date: Optional[datetime]) -> int:
        """Days since last payment."""
        if not last_payment_date:
            return 365  # Max value for never-paid
        return max(0, (self.reference_date - last_payment_date).days)
    
    def compute_account_age(self, open_date: datetime) -> int:
        """Account age in months."""
        delta = self.reference_date - open_date
        return max(1, int(delta.days / 30))
    
    def transform_single(self, record: dict) -> dict:
        """
        Transform a single account record into features.
        
        Args:
            record: Raw account data
            
        Returns:
            Feature vector as dict
        """
        features = {
            'account_id': record.get('account_id', 'unknown'),
            'days_past_due': self.compute_days_past_due(
                record.get('due_date', self.reference_date)
            ),
            'outstanding_balance': float(record.get('outstanding_balance', 0)),
            'payment_history_score': self.compute_payment_history_score(
                record.get('payment_history', [])
            ),
            'contact_attempts': int(record.get('contact_attempts', 0)),
            'last_payment_days_ago': self.compute_last_payment_days(
                record.get('last_payment_date')
            ),
            'account_age_months': self.compute_account_age(
                record.get('open_date', self.reference_date - timedelta(days=365))
            ),
        }
        
        return features
    
    def transform_batch(self, records: list[dict]) -> pd.DataFrame:
        """
        Transform multiple records into feature DataFrame.
        
        Args:
            records: List of raw account data
            
        Returns:
            DataFrame with feature columns
        """
        features = [self.transform_single(r) for r in records]
        return pd.DataFrame(features)
    
    def validate_features(self, features: dict) -> list[str]:
        """
        Validate feature vector.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        for name, expected_type in self.FEATURE_SCHEMA.items():
            if name not in features:
                errors.append(f"Missing feature: {name}")
            elif not isinstance(features[name], expected_type):
                errors.append(f"Invalid type for {name}: expected {expected_type}")
        
        # Range validations
        if features.get('payment_history_score', 0) < 0 or features.get('payment_history_score', 0) > 1:
            errors.append("payment_history_score must be between 0 and 1")
        
        if features.get('outstanding_balance', 0) < 0:
            errors.append("outstanding_balance cannot be negative")
        
        return errors


def main():
    """Demo pipeline execution."""
    logger.info("Feature Pipeline Demo")
    
    # Sample raw data
    sample_records = [
        {
            'account_id': 'ACC001',
            'due_date': datetime.utcnow() - timedelta(days=45),
            'outstanding_balance': 1250.00,
            'payment_history': [{'on_time': True}, {'on_time': True}, {'on_time': False}],
            'contact_attempts': 3,
            'last_payment_date': datetime.utcnow() - timedelta(days=60),
            'open_date': datetime.utcnow() - timedelta(days=730),
        },
        {
            'account_id': 'ACC002',
            'due_date': datetime.utcnow() - timedelta(days=15),
            'outstanding_balance': 500.00,
            'payment_history': [{'on_time': True}, {'on_time': True}],
            'contact_attempts': 1,
            'last_payment_date': datetime.utcnow() - timedelta(days=20),
            'open_date': datetime.utcnow() - timedelta(days=1095),
        },
    ]
    
    pipeline = FeaturePipeline()
    df = pipeline.transform_batch(sample_records)
    
    logger.info("Generated features:")
    print(df.to_string())
    
    return df


if __name__ == "__main__":
    main()
