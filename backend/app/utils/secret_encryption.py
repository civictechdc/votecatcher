"""Encryption helpers for secrets stored at rest (e.g. provider API keys).

Storage format: ``enc:v1:<fernet-token>``. The key comes from the
``PROVIDER_CONFIG_SECRET`` setting; plaintext values without the versioned
prefix are treated as unreadable (fail closed) so legacy or unencrypted
rows are never silently used.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.settings import get_settings

_ENC_PREFIX = "enc:v1:"


def generate_key() -> bytes:
    """Generate a new Fernet key (for setup tooling and tests)."""
    return Fernet.generate_key()


def _get_fernet() -> Fernet:
    """Build a Fernet from PROVIDER_CONFIG_SECRET; raise if unset."""
    secret = get_settings().provider_config_secret
    if secret is None or not secret.get_secret_value():
        raise RuntimeError(
            "PROVIDER_CONFIG_SECRET is not set; cannot encrypt or decrypt "
            "stored provider credentials. Generate a key with "
            "'python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"' and set it in the "
            "environment."
        )
    return Fernet(secret.get_secret_value().encode())


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret into the versioned at-rest format."""
    if not plaintext:
        raise ValueError("Cannot encrypt an empty secret")
    token = _get_fernet().encrypt(plaintext.encode()).decode()
    return f"{_ENC_PREFIX}{token}"


def decrypt_secret(value: str) -> str:
    """Decrypt a versioned secret.

    Raises:
        ValueError: If the value is not ``enc:v1:``-prefixed (legacy
            plaintext must not be used) or cannot be decrypted with the
            configured key (fail closed for both cases).
    """
    if not value.startswith(_ENC_PREFIX):
        raise ValueError(
            "Stored provider credential is not in the encrypted format "
            "(missing 'enc:v1:' prefix); refusing to use it. Re-save the "
            "provider configuration to encrypt it."
        )
    try:
        return _get_fernet().decrypt(value.removeprefix(_ENC_PREFIX)).decode()
    except InvalidToken as e:
        raise ValueError(
            "Stored provider credential cannot be decrypted with the "
            "configured PROVIDER_CONFIG_SECRET (wrong or rotated key); "
            "refusing to use it."
        ) from e
