from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    stored = hash_password("секретный-пароль")
    assert stored != "секретный-пароль"
    assert verify_password("секретный-пароль", stored)
    assert not verify_password("другой", stored)
    assert not verify_password("x", "битая-строка")


def test_hashes_are_salted():
    assert hash_password("same-password") != hash_password("same-password")


def test_token_roundtrip():
    token = create_access_token(42)
    assert decode_access_token(token) == 42
    assert decode_access_token(token + "x") is None
    assert decode_access_token("not-a-token") is None
