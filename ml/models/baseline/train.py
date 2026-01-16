"""
Baseline XGBoost Model Training Script
Reproducible training with seeded randomness.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import yaml
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
OUTPUT_DIR = SCRIPT_DIR / "artifacts"


def load_config() -> dict:
    """Load training configuration."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def generate_synthetic_data(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic training data.
    In production, this will be replaced with real feature pipeline data.
    """
    np.random.seed(seed)
    
    data = {
        'days_past_due': np.random.exponential(30, n_samples).astype(int).clip(0, 365),
        'outstanding_balance': np.random.exponential(1000, n_samples).clip(100, 50000),
        'payment_history_score': np.random.beta(5, 2, n_samples),
        'contact_attempts': np.random.poisson(3, n_samples).clip(0, 20),
        'last_payment_days_ago': np.random.exponential(45, n_samples).astype(int).clip(0, 365),
        'account_age_months': np.random.exponential(24, n_samples).astype(int).clip(1, 120),
    }
    
    df = pd.DataFrame(data)
    
    # Generate labels based on rules (simulating real outcomes)
    labels = []
    for _, row in df.iterrows():
        if row['days_past_due'] > 90 and row['payment_history_score'] < 0.3:
            labels.append('write_off')
        elif row['days_past_due'] > 60 or row['outstanding_balance'] > 5000:
            labels.append('escalate')
        elif row['days_past_due'] < 30 and row['payment_history_score'] > 0.7:
            labels.append('recover')
        else:
            labels.append('monitor')
    
    df['label'] = labels
    
    return df


def train_model(config: dict) -> tuple:
    """
    Train XGBoost model.
    Returns (model, label_encoder, metrics)
    """
    logger.info("Generating training data...")
    df = generate_synthetic_data(
        n_samples=5000,
        seed=config['training']['random_seed']
    )
    
    # Prepare features and labels
    feature_names = [f['name'] for f in config['features']]
    X = df[feature_names]
    y = df['label']
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size=config['training']['test_size'],
        random_state=config['training']['random_seed'],
        stratify=y_encoded
    )
    
    logger.info(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    logger.info(f"Label distribution: {dict(pd.Series(y).value_counts())}")
    
    # Train XGBoost
    params = config['hyperparameters'].copy()
    params['objective'] = 'multi:softprob'
    params['num_class'] = len(le.classes_)
    
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_names)
    dtest = xgb.DMatrix(X_test, label=y_test, feature_names=feature_names)
    
    logger.info("Training XGBoost model...")
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=params['n_estimators'],
        evals=[(dtrain, 'train'), (dtest, 'eval')],
        early_stopping_rounds=config['training']['early_stopping_rounds'],
        verbose_eval=10
    )
    
    # Calculate metrics
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    
    y_pred = model.predict(dtest).argmax(axis=1)
    
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'f1_weighted': float(f1_score(y_test, y_pred, average='weighted')),
        'precision_weighted': float(precision_score(y_test, y_pred, average='weighted')),
        'recall_weighted': float(recall_score(y_test, y_pred, average='weighted')),
    }
    
    logger.info(f"Metrics: {metrics}")
    
    return model, le, metrics, feature_names


def save_artifacts(model, label_encoder, metrics: dict, feature_names: list, config: dict):
    """Save model and metadata."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = OUTPUT_DIR / "model.json"
    model.save_model(str(model_path))
    logger.info(f"Model saved to {model_path}")
    
    # Save metadata
    metadata = {
        'version': config['model']['version'],
        'name': config['model']['name'],
        'created_at': datetime.utcnow().isoformat(),
        'git_commit': os.getenv('GIT_COMMIT', 'local'),
        'feature_names': feature_names,
        'label_classes': list(label_encoder.classes_),
        'metrics': metrics,
        'hyperparameters': config['hyperparameters'],
    }
    
    metadata_path = OUTPUT_DIR / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to {metadata_path}")
    
    # Save label encoder classes
    labels_path = OUTPUT_DIR / "labels.json"
    with open(labels_path, 'w') as f:
        json.dump({'classes': list(label_encoder.classes_)}, f)
    
    return metadata


def main():
    """Main training entrypoint."""
    logger.info("=" * 60)
    logger.info("INFLOW AI - Baseline Model Training")
    logger.info("=" * 60)
    
    config = load_config()
    logger.info(f"Model: {config['model']['name']} v{config['model']['version']}")
    
    model, le, metrics, feature_names = train_model(config)
    metadata = save_artifacts(model, le, metrics, feature_names, config)
    
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info(f"F1 Score: {metrics['f1_weighted']:.4f}")
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info("=" * 60)
    
    return metadata


if __name__ == "__main__":
    main()
