#!/usr/bin/env python3
"""Small smoke script to exercise token generation and verification."""
import os
from dotenv import load_dotenv

load_dotenv()

from mkdocs_msal_auth.auth import generate_signed_token, verify_signed_token


def main():
    email = os.environ.get('SMOKE_TEST_EMAIL', 'user@example.com')
    token = generate_signed_token({'email': email})
    print('Generated token:', token)

    payload = verify_signed_token(token)
    print('Verified payload:', payload)


if __name__ == '__main__':
    main()
