"""
MLflow Registry Integration
Manages model versioning, promotion, and rollback.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.models import infer_signature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = "inflow-baseline"


class ModelRegistry:
    """
    MLflow Model Registry manager.
    Handles versioning, promotion, and rollback.
    """
    
    STAGES = ["None", "Staging", "Production", "Archived"]
    
    def __init__(self, tracking_uri: str = MLFLOW_TRACKING_URI):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()
        self.tracking_uri = tracking_uri
        logger.info(f"Connected to MLflow at {tracking_uri}")
    
    def register_model(
        self,
        model_path: str,
        model_name: str = MODEL_NAME,
        metrics: Optional[dict] = None,
        params: Optional[dict] = None,
        tags: Optional[dict] = None
    ) -> str:
        """
        Register a new model version.
        
        Args:
            model_path: Path to model artifacts
            model_name: Name in registry
            metrics: Training metrics
            params: Hyperparameters
            tags: Additional tags
            
        Returns:
            Version string
        """
        with mlflow.start_run() as run:
            # Log parameters
            if params:
                mlflow.log_params(params)
            
            # Log metrics
            if metrics:
                mlflow.log_metrics(metrics)
            
            # Log model
            mlflow.log_artifacts(model_path, "model")
            
            # Register model
            model_uri = f"runs:/{run.info.run_id}/model"
            result = mlflow.register_model(model_uri, model_name)
            
            # Add tags
            if tags:
                for key, value in tags.items():
                    self.client.set_model_version_tag(
                        model_name, result.version, key, value
                    )
            
            logger.info(f"Registered {model_name} v{result.version}")
            return result.version
    
    def promote_model(
        self,
        model_name: str,
        version: str,
        stage: str = "Staging"
    ) -> bool:
        """
        Promote model to a stage.
        
        Args:
            model_name: Name in registry
            version: Version to promote
            stage: Target stage (Staging, Production)
            
        Returns:
            Success boolean
        """
        if stage not in self.STAGES:
            raise ValueError(f"Invalid stage: {stage}. Must be one of {self.STAGES}")
        
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=(stage == "Production")
        )
        
        logger.info(f"Promoted {model_name} v{version} to {stage}")
        return True
    
    def rollback_model(
        self,
        model_name: str,
        stage: str = "Production"
    ) -> Optional[str]:
        """
        Rollback to previous version in stage.
        
        Args:
            model_name: Name in registry
            stage: Stage to rollback
            
        Returns:
            New active version or None
        """
        # Get archived versions
        versions = self.client.search_model_versions(f"name='{model_name}'")
        archived = [v for v in versions if v.current_stage == "Archived"]
        
        if not archived:
            logger.error("No archived versions to rollback to")
            return None
        
        # Get most recent archived
        latest_archived = max(archived, key=lambda v: int(v.version))
        
        # Promote it back
        self.promote_model(model_name, latest_archived.version, stage)
        
        logger.info(f"Rolled back {model_name} to v{latest_archived.version}")
        return latest_archived.version
    
    def get_model_version(
        self,
        model_name: str,
        stage: str = "Production"
    ) -> Optional[str]:
        """Get current version for a stage."""
        versions = self.client.get_latest_versions(model_name, stages=[stage])
        if versions:
            return versions[0].version
        return None
    
    def get_model_uri(
        self,
        model_name: str,
        stage: str = "Production"
    ) -> Optional[str]:
        """Get model URI for serving."""
        version = self.get_model_version(model_name, stage)
        if version:
            return f"models:/{model_name}/{stage}"
        return None
    
    def list_versions(self, model_name: str) -> list:
        """List all versions of a model."""
        versions = self.client.search_model_versions(f"name='{model_name}'")
        return [
            {
                "version": v.version,
                "stage": v.current_stage,
                "created": v.creation_timestamp,
                "run_id": v.run_id
            }
            for v in versions
        ]


def main():
    """Demo registry operations."""
    logger.info("MLflow Registry Demo")
    
    registry = ModelRegistry()
    
    # List existing versions
    versions = registry.list_versions(MODEL_NAME)
    logger.info(f"Existing versions: {versions}")
    
    # Get current production model
    prod_version = registry.get_model_version(MODEL_NAME, "Production")
    logger.info(f"Production version: {prod_version}")


if __name__ == "__main__":
    main()
