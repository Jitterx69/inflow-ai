"""
SHAP Explainability Module
Generates feature importance explanations for model predictions.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
import shap
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent / "models" / "baseline" / "artifacts"
OUTPUT_DIR = Path(__file__).parent / "artifacts"


def load_model():
    """Load trained model."""
    model_path = MODEL_DIR / "model.json"
    metadata_path = MODEL_DIR / "metadata.json"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found. Run training first.")
    
    model = xgb.Booster()
    model.load_model(str(model_path))
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    return model, metadata


def generate_sample_data(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """Generate sample data for SHAP analysis."""
    np.random.seed(seed)
    
    return pd.DataFrame({
        'days_past_due': np.random.exponential(30, n_samples).astype(int).clip(0, 365),
        'outstanding_balance': np.random.exponential(1000, n_samples).clip(100, 50000),
        'payment_history_score': np.random.beta(5, 2, n_samples),
        'contact_attempts': np.random.poisson(3, n_samples).clip(0, 20),
        'last_payment_days_ago': np.random.exponential(45, n_samples).astype(int).clip(0, 365),
        'account_age_months': np.random.exponential(24, n_samples).astype(int).clip(1, 120),
    })


def compute_shap_values(model, X: pd.DataFrame, feature_names: list) -> tuple:
    """
    Compute SHAP values for the dataset.
    
    Returns:
        (explainer, shap_values)
    """
    # Create DMatrix
    dmatrix = xgb.DMatrix(X, feature_names=feature_names)
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    
    # Compute SHAP values
    shap_values = explainer.shap_values(X)
    
    return explainer, shap_values


def generate_summary_plot(shap_values, X: pd.DataFrame, output_path: Path):
    """Generate and save SHAP summary plot."""
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, show=False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Summary plot saved to {output_path}")


def generate_feature_importance(shap_values, feature_names: list) -> dict:
    """Compute global feature importance from SHAP values."""
    # For multi-class, shap_values is a list of arrays
    if isinstance(shap_values, list):
        # Average absolute SHAP values across all classes
        mean_abs_shap = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    else:
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    # Normalize to sum to 1
    total = mean_abs_shap.sum()
    normalized = mean_abs_shap / total if total > 0 else mean_abs_shap
    
    importance = {
        name: float(normalized[i])
        for i, name in enumerate(feature_names)
    }
    
    # Sort by importance
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    return importance


def explain_single(model, features: dict, feature_names: list, label_classes: list) -> dict:
    """
    Explain a single prediction.
    
    Args:
        model: Trained XGBoost model
        features: Feature dict for single instance
        feature_names: List of feature names
        label_classes: List of class labels
        
    Returns:
        Explanation dict with prediction and feature contributions
    """
    # Prepare input
    X = pd.DataFrame([features])[feature_names]
    dmatrix = xgb.DMatrix(X, feature_names=feature_names)
    
    # Get prediction
    proba = model.predict(dmatrix)[0]
    pred_idx = proba.argmax()
    pred_label = label_classes[pred_idx]
    
    # Compute SHAP
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Get SHAP values for predicted class
    if isinstance(shap_values, list):
        sv = shap_values[pred_idx][0]
    else:
        sv = shap_values[0]
    
    # Build explanation
    contributions = []
    for i, name in enumerate(feature_names):
        contributions.append({
            'feature': name,
            'value': float(features[name]),
            'shap_value': float(sv[i]),
            'contribution': 'positive' if sv[i] > 0 else 'negative' if sv[i] < 0 else 'neutral'
        })
    
    # Sort by absolute SHAP value
    contributions.sort(key=lambda x: abs(x['shap_value']), reverse=True)
    
    return {
        'prediction': pred_label,
        'confidence': float(proba[pred_idx]),
        'probabilities': {label_classes[i]: float(p) for i, p in enumerate(proba)},
        'feature_contributions': contributions
    }


def main():
    """Generate SHAP summary and save artifacts."""
    logger.info("=" * 60)
    logger.info("INFLOW AI - SHAP Explainability Analysis")
    logger.info("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    model, metadata = load_model()
    feature_names = metadata['feature_names']
    
    logger.info("Generating sample data...")
    X = generate_sample_data(n_samples=100)
    X = X[feature_names]  # Ensure column order
    
    logger.info("Computing SHAP values...")
    explainer, shap_values = compute_shap_values(model, X, feature_names)
    
    logger.info("Generating summary plot...")
    generate_summary_plot(shap_values, X, OUTPUT_DIR / "shap_summary.png")
    
    logger.info("Computing feature importance...")
    importance = generate_feature_importance(shap_values, feature_names)
    
    # Save importance
    with open(OUTPUT_DIR / "feature_importance.json", 'w') as f:
        json.dump(importance, f, indent=2)
    
    logger.info("=" * 60)
    logger.info("Feature Importance (SHAP-based):")
    for name, imp in importance.items():
        logger.info(f"  {name}: {imp:.4f}")
    logger.info("=" * 60)
    
    return importance


if __name__ == "__main__":
    main()
