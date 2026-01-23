from typing import Dict, Any
import random

class ViabilityScorer:
    """
    Scores ideas based on alignment with creator topics.
    """
    
    def score_idea(self, idea: Dict[str, Any], creator_profile: Dict[str, Any]) -> float:
        """
        Returns a score 0-100.
        """
        base_score = 0.5
        
        idea_topics = set(t.lower() for t in idea.get("topics", []))
        creator_topics = set(t.lower() for t in creator_profile.get("primary_topics", []))
        
        # Check overlap
        if not idea_topics:
            # No topics? Neutral.
            alignment = 0.0
        elif idea_topics.intersection(creator_topics):
            # Strong alignment
            alignment = 0.3
        else:
            # topic mismatch
            alignment = -0.1
            
        final_score = base_score + alignment
        
        # Add a tiny bit of noise/AI-magic simulation (0 to 5%)
        noise = random.uniform(0, 0.05)
        final_score += noise
        
        return min(100.0, max(0.0, final_score * 100))
