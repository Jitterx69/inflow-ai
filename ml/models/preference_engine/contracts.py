from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class FeedbackType(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"

class RejectionReason(str, Enum):
    TOO_RISKY = "too_risky"
    OFF_BRAND = "off_brand"
    BORING = "boring"
    OTHER = "other"

class PreferenceUpdate(BaseModel):
    creator_id: str
    content_id: str
    feedback: FeedbackType
    rejection_reason: Optional[RejectionReason] = None
    content_risk_score: float = Field(..., ge=0.0, le=1.0)

class CreatorState(BaseModel):
    creator_id: str
    risk_tolerance: float = Field(..., ge=0.0, le=1.0)
