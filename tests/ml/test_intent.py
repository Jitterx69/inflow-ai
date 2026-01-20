import pytest
from ml.models.intent_routing.classifier import IntentClassifier
from ml.models.intent_routing.contracts import IntentRequest, IntentType

@pytest.fixture
def classifier():
    return IntentClassifier()

def test_ambiguity_detection(classifier):
    req = IntentRequest(query="help")
    resp = classifier.predict(req)
    assert resp.ambiguity_flag is True
    assert resp.intent_type == IntentType.UNKNOWN

def test_creation_intent(classifier):
    req = IntentRequest(query="Write a LinkedIn post about AI")
    resp = classifier.predict(req)
    assert resp.intent_type == IntentType.CREATION
    assert resp.confidence > 0.8

def test_decision_intent(classifier):
    req = IntentRequest(query="Should I post this today?")
    resp = classifier.predict(req)
    assert resp.intent_type == IntentType.DECISION

def test_planning_intent(classifier):
    req = IntentRequest(query="Create a content calendar for next week")
    resp = classifier.predict(req)
    assert resp.intent_type == IntentType.PLANNING

def test_reflection_intent(classifier):
    req = IntentRequest(query="How can I grow my audience?")
    resp = classifier.predict(req)
    # "grow" might be ambiguous if alone, but with context "How can I..." len > 15
    assert resp.intent_type == IntentType.REFLECTION
