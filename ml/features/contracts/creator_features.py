from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int32, String, Array

# =============================================================================
# Entities
# =============================================================================

creator = Entity(
    name="creator",
    join_keys=["creator_id"],
    description="Unique creator identifier"
)

# =============================================================================
# Data Sources (Mocked for now via Parquet)
# =============================================================================

creator_identity_source = FileSource(
    path="data/creator_identity.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_at"
)

# =============================================================================
# Feature Views
# =============================================================================

creator_identity_v1 = FeatureView(
    name="creator_identity_v1",
    entities=[creator],
    ttl=timedelta(days=365),  # Identity is long-lived
    schema=[
        Field(name="posting_cadence_days", dtype=Int32),
        Field(name="tone_vector", dtype=Array(Float32)), # Embedding of tone
        Field(name="primary_topics", dtype=Array(String)),
        Field(name="growth_stage", dtype=String), # ASPIRING, GROWING, PRO
    ],
    source=creator_identity_source,
    online=True,
    tags={"owner": "richa", "layer": "hippocampus"}
)

creator_preferences_v1 = FeatureView(
    name="creator_preferences_v1",
    entities=[creator],
    ttl=timedelta(days=30),
    schema=[
        Field(name="risk_tolerance", dtype=Float32), # 0.0 to 1.0
        Field(name="preferred_platforms", dtype=Array(String)),
    ],
    source=creator_identity_source,
    online=True,
    tags={"owner": "richa", "layer": "hippocampus"}
)
