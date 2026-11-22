import pytest

from app.security.crypto import EncryptionError, decrypt, encrypt


def test_encrypt_roundtrip_and_not_plaintext():
    token = "1//refresh-token-value"
    enc = encrypt(token)
    assert token not in enc
    assert decrypt(enc) == token


def test_tampered_ciphertext_is_rejected():
    enc = encrypt("secret")
    tampered = enc[:-4] + ("AAAA" if not enc.endswith("AAAA") else "BBBB")
    with pytest.raises(EncryptionError):
        decrypt(tampered)
