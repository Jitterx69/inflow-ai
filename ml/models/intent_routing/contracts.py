from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class IntentType(str, Enum):
    DECISION = "decision_seeking"
    CREATION = "content_creation"
    PLANNING = "strategic_planning"
    REFLECTION = "reflection_and_growth"
    UNKNOWN = "unknown"

class IntentRequest(BaseModel):
    query: str = Field(..., description="The user's natural language query")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")

class IntentResponse(BaseModel):
    intent_type: IntentType = Field(..., description="The classified intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the classification")
    ambiguity_flag: bool = Field(..., description="True if the query is too vague to act upon")
    reasoning: Optional[str] = Field(None, description="Explanation for the classification/ambiguity")
