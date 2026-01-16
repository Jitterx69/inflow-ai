"""
Feast Registry Manager
Handles feature store operations.
"""

import os
import logging
from pathlib import Path

from feast import FeatureStore
from feast.repo_config import load_repo_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEATURE_STORE_PATH = Path(__file__).parent


class FeastRegistry:
    """
    Feast feature store manager.
    Ensures training/serving parity.
    """
    
    def __init__(self, repo_path: str = str(FEATURE_STORE_PATH)):
        self.repo_path = repo_path
        self.store = FeatureStore(repo_path=repo_path)
        logger.info(f"Initialized Feast registry at {repo_path}")
    
    def apply(self):
        """Apply feature definitions to registry."""
        self.store.apply([])  # Apply all definitions in repo
        logger.info("Applied feature definitions")
    
    def materialize(self, start_date, end_date):
        """Materialize features to online store."""
        self.store.materialize(start_date=start_date, end_date=end_date)
        logger.info(f"Materialized features from {start_date} to {end_date}")
    
    def get_online_features(self, entity_rows: list[dict], features: list[str]) -> dict:
        """
        Get features from online store.
        
        Args:
            entity_rows: List of entity dicts [{"account_id": "ACC001"}]
            features: List of feature refs ["account_features:days_past_due"]
            
        Returns:
            Feature values dict
        """
        feature_refs = features if features else [
            "account_features:days_past_due",
            "account_features:outstanding_balance",
            "account_features:contact_attempts",
            "account_features:last_payment_days_ago",
            "account_features:account_age_months",
            "payment_history:payment_history_score",
        ]
        
        response = self.store.get_online_features(
            features=feature_refs,
            entity_rows=entity_rows
        )
        
        return response.to_dict()
    
    def get_historical_features(self, entity_df, features: list[str]):
        """
        Get historical features for training.
        
        Args:
            entity_df: DataFrame with entity keys and timestamps
            features: List of feature refs
            
        Returns:
            DataFrame with features
        """
        return self.store.get_historical_features(
            entity_df=entity_df,
            features=features
        ).to_df()
    
    def list_feature_views(self) -> list:
        """List all registered feature views."""
        views = self.store.list_feature_views()
        return [
            {
                "name": v.name,
                "entities": [e.name for e in v.entities],
                "features": [f.name for f in v.features],
                "ttl": str(v.ttl)
            }
            for v in views
        ]


def main():
    """Demo feature store operations."""
    logger.info("Feast Registry Demo")
    
    registry = FeastRegistry()
    
    # List feature views
    views = registry.list_feature_views()
    logger.info(f"Feature views: {views}")


if __name__ == "__main__":
    main()
