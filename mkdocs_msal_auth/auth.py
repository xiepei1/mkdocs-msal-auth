"""Authentication helpers for mkdocs-google-auth.

Provides functions to issue and verify server-signed tokens so the Flask
frontend and the MkDocs hooks can share the same verification logic.
"""
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


def _get_serializer(salt: str = 'mkdocs-google-auth') -> URLSafeTimedSerializer:
    secret = os.environ.get('SECRET_KEY', 'dev-secret-key')
    return URLSafeTimedSerializer(secret, salt=salt)


def generate_signed_token(payload: dict, expires_in: int | None = None) -> str:
    """Generate a signed token with the given payload (e.g. {'email': ...}).

    The token is URL-safe. The expiration is enforced during verification via
    the `max_age` argument of `loads`.
    """
    s = _get_serializer()
    return s.dumps(payload)


def verify_signed_token(token: str) -> dict:
    """Verify a signed token and return the payload.

    Raises SignatureExpired or BadSignature on error.
    """
    s = _get_serializer()
    max_age = int(os.environ.get('TOKEN_EXPIRES_SECONDS', 3600))
    data = s.loads(token, max_age=max_age)
    return data
