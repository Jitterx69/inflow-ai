import pytest
from ml.models.preference_engine import BayesianUpdater, PreferenceUpdate, CreatorState, FeedbackType, RejectionReason

@pytest.fixture
def updater():
    return BayesianUpdater()

def test_risk_reduction_on_rejection(updater):
    current = CreatorState(creator_id="123", risk_tolerance=0.8)
    update = PreferenceUpdate(
        creator_id="123",
        content_id="post_1",
        feedback=FeedbackType.REJECTED,
        rejection_reason=RejectionReason.TOO_RISKY,
        content_risk_score=0.9
    )
    
    new_state = updater.process_update(current, update)
    # 0.8 * 0.8 = 0.64
    assert new_state.risk_tolerance == 0.64

def test_risk_boost_on_acceptance(updater):
    current = CreatorState(creator_id="123", risk_tolerance=0.5)
    update = PreferenceUpdate(
        creator_id="123",
        content_id="post_2",
        feedback=FeedbackType.ACCEPTED,
        content_risk_score=0.8 # High risk content accepted
    )
    
    new_state = updater.process_update(current, update)
    # 0.5 * 1.1 = 0.55
    assert new_state.risk_tolerance == 0.55

def test_no_change_on_low_risk_acceptance(updater):
    current = CreatorState(creator_id="123", risk_tolerance=0.5)
    update = PreferenceUpdate(
        creator_id="123",
        content_id="post_3",
        feedback=FeedbackType.ACCEPTED,
        content_risk_score=0.2 # Safe content
    )
    
    new_state = updater.process_update(current, update)
    assert new_state.risk_tolerance == 0.5
