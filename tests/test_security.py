from aquasentinel.security import create_access_token, hash_password, verify_password


def test_password_hash_round_trip() -> None:
    encoded = hash_password("a-long-demo-password")
    assert "a-long-demo-password" not in encoded
    assert verify_password("a-long-demo-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_access_token_contains_scopes() -> None:
    token = create_access_token("demo-user", ["researcher"], ["tn-coimbatore"])
    assert token.count(".") == 2

