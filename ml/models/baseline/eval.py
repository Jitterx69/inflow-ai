"""
Baseline Model Evaluation Script
Evaluates trained model on test data.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"


def load_model():
    """Load trained model and metadata."""
    model_path = ARTIFACTS_DIR / "model.json"
    metadata_path = ARTIFACTS_DIR / "metadata.json"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run train.py first.")
    
    model = xgb.Booster()
    model.load_model(str(model_path))
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    return model, metadata


def generate_test_data(n_samples: int = 1000, seed: int = 123) -> pd.DataFrame:
    """Generate test data with different seed than training."""
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
    
    # Generate labels
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


def evaluate(model, metadata: dict, df: pd.DataFrame) -> dict:
    """Run evaluation and return metrics."""
    feature_names = metadata['feature_names']
    label_classes = metadata['label_classes']
    
    X = df[feature_names]
    y_true = df['label']
    
    # Convert labels to indices
    label_to_idx = {label: idx for idx, label in enumerate(label_classes)}
    y_true_idx = [label_to_idx[label] for label in y_true]
    
    # Predict
    dtest = xgb.DMatrix(X, feature_names=feature_names)
    y_pred_proba = model.predict(dtest)
    y_pred_idx = y_pred_proba.argmax(axis=1)
    y_pred = [label_classes[idx] for idx in y_pred_idx]
    
    # Metrics
    metrics = {
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'f1_weighted': float(f1_score(y_true, y_pred, average='weighted')),
        'precision_weighted': float(precision_score(y_true, y_pred, average='weighted')),
        'recall_weighted': float(recall_score(y_true, y_pred, average='weighted')),
    }
    
    # Per-class metrics
    report = classification_report(y_true, y_pred, output_dict=True)
    metrics['per_class'] = {
        label: {
            'precision': report[label]['precision'],
            'recall': report[label]['recall'],
            'f1': report[label]['f1-score'],
            'support': report[label]['support']
        }
        for label in label_classes
    }
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=label_classes)
    metrics['confusion_matrix'] = {
        'labels': label_classes,
        'matrix': cm.tolist()
    }
    
    return metrics


def main():
    """Main evaluation entrypoint."""
    logger.info("=" * 60)
    logger.info("INFLOW AI - Baseline Model Evaluation")
    logger.info("=" * 60)
    
    model, metadata = load_model()
    logger.info(f"Model: {metadata['name']} v{metadata['version']}")
    logger.info(f"Training metrics: {metadata['metrics']}")
    
    logger.info("Generating test data...")
    df = generate_test_data(n_samples=1000, seed=123)
    
    logger.info("Running evaluation...")
    metrics = evaluate(model, metadata, df)
    
    # Save evaluation results
    eval_path = ARTIFACTS_DIR / "evaluation.json"
    with open(eval_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("=" * 60)
    logger.info("Evaluation Results:")
    logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
    logger.info(f"  F1 Score:  {metrics['f1_weighted']:.4f}")
    logger.info(f"  Precision: {metrics['precision_weighted']:.4f}")
    logger.info(f"  Recall:    {metrics['recall_weighted']:.4f}")
    logger.info("=" * 60)
    
    # Print classification report
    logger.info("\nPer-class metrics:")
    for label, m in metrics['per_class'].items():
        logger.info(f"  {label}: P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f}")
    
    return metrics


if __name__ == "__main__":
    main()
