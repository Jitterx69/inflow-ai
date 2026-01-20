from ml.features.contracts.creator_features import creator_identity_v1, creator_preferences_v1

def test_feature_contracts_load():
    """
    Simple smoke test to ensure Feast definitions are valid Python code.
    """
    assert creator_identity_v1.name == "creator_identity_v1"
    assert creator_preferences_v1.name == "creator_preferences_v1"
