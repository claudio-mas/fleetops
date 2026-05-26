import pyotp

from app.services.mfa_service import MFAService


def test_generate_secret():
    """Test TOTP secret generation creates 32-char base32 string."""
    secret = MFAService.generate_secret()
    assert secret
    assert len(secret) == 32
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=" for c in secret)


def test_generate_secret_randomness():
    """Test generated secrets are unique."""
    secret1 = MFAService.generate_secret()
    secret2 = MFAService.generate_secret()
    assert secret1 != secret2


def test_get_totp():
    """Test getting TOTP object from secret."""
    secret = "JBSWY3DPEBLW64TMMQ======"
    totp = MFAService.get_totp(secret)
    assert isinstance(totp, pyotp.TOTP)


def test_provisioning_uri():
    """Test provisioning URI generation for QR code."""
    secret = "JBSWY3DPEBLW64TMMQ======"
    uri = MFAService.get_provisioning_uri(secret, "user@example.com")

    assert "otpauth://totp/" in uri
    assert "user%40example.com" in uri or "user@example.com" in uri
    assert "FleetOps" in uri


def test_provisioning_uri_custom_issuer():
    """Test provisioning URI with custom issuer."""
    secret = "JBSWY3DPEBLW64TMMQ======"
    uri = MFAService.get_provisioning_uri(
        secret, "user@example.com", issuer="CustomApp"
    )

    assert "CustomApp" in uri


def test_qr_code_generation():
    """Test QR code generates as data URI."""
    secret = "JBSWY3DPEBLW64TMMQ======"
    uri = MFAService.get_provisioning_uri(secret, "user@example.com")
    qr_code = MFAService.generate_qr_code(uri)

    assert qr_code.startswith("data:image/png;base64,")
    assert len(qr_code) > 100


def test_verify_token_valid():
    """Test verifying valid TOTP token."""
    secret = "JBSWY3DPEBLW64TMMQ======"
    totp = MFAService.get_totp(secret)
    token = totp.now()

    assert MFAService.verify_token(secret, token)


def test_verify_token_invalid():
    """Test verifying invalid TOTP token."""
    secret = "JBSWY3DPEBLW64TMMQ======"

    assert not MFAService.verify_token(secret, "000000")


def test_verify_token_with_window():
    """Test verify_token uses window for clock skew tolerance."""
    secret = "JBSWY3DPEBLW64TMMQ======"
    totp = MFAService.get_totp(secret)
    token = totp.now()
    assert MFAService.verify_token(secret, token, window=1)
