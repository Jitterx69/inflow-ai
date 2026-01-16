"""
Account Feature Definitions
Training/Serving parity enforced via Feast.
"""

from datetime import timedelta

from feast import Entity, Feature, FeatureView, Field, FileSource
from feast.types import Float32, Int32, String


# =============================================================================
# Entities
# =============================================================================

account = Entity(
    name="account",
    join_keys=["account_id"],
    description="Unique account identifier"
)


# =============================================================================
# Data Sources
# =============================================================================

account_features_source = FileSource(
    path="data/account_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_at"
)

payment_history_source = FileSource(
    path="data/payment_history.parquet",
    timestamp_field="event_timestamp"
)


# =============================================================================
# Feature Views
# =============================================================================

account_features = FeatureView(
    name="account_features",
    entities=[account],
    ttl=timedelta(days=1),
    schema=[
        Field(name="days_past_due", dtype=Int32),
        Field(name="outstanding_balance", dtype=Float32),
        Field(name="contact_attempts", dtype=Int32),
        Field(name="last_payment_days_ago", dtype=Int32),
        Field(name="account_age_months", dtype=Int32),
    ],
    source=account_features_source,
    online=True,
    tags={"owner": "ml-team", "version": "v1"}
)

payment_history_features = FeatureView(
    name="payment_history",
    entities=[account],
    ttl=timedelta(days=7),
    schema=[
        Field(name="payment_history_score", dtype=Float32),
        Field(name="total_payments", dtype=Int32),
        Field(name="missed_payments", dtype=Int32),
        Field(name="average_payment_amount", dtype=Float32),
    ],
    source=payment_history_source,
    online=True,
    tags={"owner": "ml-team", "version": "v1"}
)
