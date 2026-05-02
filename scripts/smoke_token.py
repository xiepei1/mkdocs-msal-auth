#!/usr/bin/env python3
"""Small smoke script to validate local MSAL configuration."""

import os

from dotenv import load_dotenv

load_dotenv()


def main():
    """Validate that required MSAL environment variables are available."""
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    tenant_id = os.environ.get('TENANT_ID')
    authority = os.environ.get('AUTHORITY') or (
        f'https://login.microsoftonline.com/{tenant_id}' if tenant_id else None
    )

    missing = [
        name
        for name, value in {
            'CLIENT_ID': client_id,
            'CLIENT_SECRET': client_secret,
            'TENANT_ID or AUTHORITY': tenant_id or os.environ.get('AUTHORITY'),
        }.items()
        if not value
    ]

    if missing:
        print('Missing required environment variables:', ', '.join(missing))
        raise SystemExit(1)

    print('MSAL configuration looks good.')
    print('Authority:', authority)
    print('Client ID prefix:', f"{client_id[:8]}..." if client_id else 'n/a')


if __name__ == '__main__':
    main()
