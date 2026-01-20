class AmbiguityDetector:
    """
    Detects if a user query is too vague to be actionable.
    """
    
    def __init__(self, min_length_threshold: int = 15):
        self.min_length_threshold = min_length_threshold

    def is_ambiguous(self, query: str) -> bool:
        """
        Simple heuristic: Short queries without specific keywords are ambiguous.
        TODO: Replace with LLM-based specificity score.
        """
        stripped_query = query.strip()
        
        # Rule 1: Too short
        if len(stripped_query) < self.min_length_threshold:
            return True
            
        # Rule 2: Generic distinct words check (placeholder logic)
        # If it's just "help me" or "grow", it's ambiguous
        if stripped_query.lower() in ["help", "help me", "grow", "start"]:
            return True
            
        return False
