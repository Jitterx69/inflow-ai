
from .contracts import IntentRequest, IntentResponse, IntentType
from .ambiguity import AmbiguityDetector

class IntentClassifier:
    def __init__(self):
        self.ambiguity_detector = AmbiguityDetector()

    def predict(self, request: IntentRequest) -> IntentResponse:
        query = request.query
        
        # 1. Check Ambiguity
        if self.ambiguity_detector.is_ambiguous(query):
            return IntentResponse(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                ambiguity_flag=True,
                reasoning="Query is too short or vague."
            )

        # 2. Heuristic Classification (Scaffolding for P3)
        # TODO: Replace with LLM call (OpenAI/Anthropic)
        query_lower = query.lower()
        
        intent = IntentType.UNKNOWN
        confidence = 0.5
        reasoning = "Default heuristic match."

        if any(w in query_lower for w in ["should", "analyze", "review", "audit"]):
            intent = IntentType.DECISION
            confidence = 0.8
            reasoning = "Detected decision/analysis keywords."
        elif any(w in query_lower for w in ["plan", "strategy", "calendar", "schedule"]):
            intent = IntentType.PLANNING
            confidence = 0.85
            reasoning = "Detected planning keywords."
        elif any(w in query_lower for w in ["reflect", "grow", "learning", "insight"]):
            intent = IntentType.REFLECTION
            confidence = 0.8
            reasoning = "Detected reflection keywords."
        elif any(w in query_lower for w in ["create", "write", "post", "draft", "caption"]):
            intent = IntentType.CREATION
            confidence = 0.9
            reasoning = "Detected creation keywords."
        
        # Fallback for unknown
        if intent == IntentType.UNKNOWN:
            reasoning = "No specific keywords matching known intents."

        return IntentResponse(
            intent_type=intent,
            confidence=confidence,
            ambiguity_flag=False,
            reasoning=reasoning
        )
