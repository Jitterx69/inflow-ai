from .contracts import PreferenceUpdate, CreatorState, FeedbackType, RejectionReason

class BayesianUpdater:
    """
    Updates creator preferences based on feedback using simple Bayesian-inspired heuristics.
    """
    
    def update_risk_tolerance(self, current_tolerance: float, update: PreferenceUpdate) -> float:
        """
        Adjusts risk tolerance based on feedback.
        """
        new_tolerance = current_tolerance

        if update.feedback == FeedbackType.REJECTED:
            if update.rejection_reason == RejectionReason.TOO_RISKY:
                # Strong penalty for explicit risk rejection
                new_tolerance = current_tolerance * 0.8
            elif update.rejection_reason == RejectionReason.BORING:
                # Slight boost if they want more edge
                new_tolerance = min(1.0, current_tolerance * 1.05)
        
        elif update.feedback == FeedbackType.ACCEPTED:
            # If they accept risky content, boost tolerance
            if update.content_risk_score > 0.7:
                new_tolerance = min(1.0, current_tolerance * 1.1)
        
        return round(new_tolerance, 4)

    def process_update(self, current_state: CreatorState, update: PreferenceUpdate) -> CreatorState:
        new_risk = self.update_risk_tolerance(current_state.risk_tolerance, update)
        
        return CreatorState(
            creator_id=current_state.creator_id,
            risk_tolerance=new_risk
        )
