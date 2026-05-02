# MkDocs + Flask + Microsoft Entra ID Authentication

This project builds documentation with MkDocs, serves the generated static site through Flask, and enforces authentication with Microsoft Entra ID (Azure AD) using MSAL for Python.

## Architecture

1. MkDocs builds static HTML into the `site/` folder.
2. Flask serves files from `site/`.
3. Unauthenticated users are redirected to Microsoft Entra ID login.
4. After successful sign-in, Flask stores the user identity in a secure session.
5. Optionally restrict access by email domain and/or specific email addresses.

## Features

- Documentation generation with MkDocs Material
- Flask server for hosting generated HTML
- Microsoft Entra ID OAuth2 authorization code flow via MSAL
- Access control using `allowed_domains` and `allowed_emails`
- Runtime configuration from environment variables (`.env` for local development)

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

Optional for local development with the `src` layout:

```bash
pip install -e .
```

2. Copy environment template and fill values:

```bash
cp .env.example .env
```

3. Build docs:

```bash
mkdocs build
```

4. Start local server:

```bash
python -m src.webapp.server
```

5. Open `http://localhost:5000`.

## Production Run (WSGI)

Use Gunicorn with the WSGI entrypoint:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 3 wsgi:app
```

Optional hardening:

- Set `SESSION_COOKIE_SECURE=true` when serving over HTTPS.
- Always set a strong `SECRET_KEY`.

## Required Environment Variables

- `CLIENT_ID`: Entra application (client) ID
- `CLIENT_SECRET`: Entra client secret
- `TENANT_ID`: Entra tenant ID
- `AUTHORITY` (optional): overrides default `https://login.microsoftonline.com/<TENANT_ID>`
- `SECRET_KEY`: Flask session signing key

## Entra App Registration

In Microsoft Entra admin center:

1. Register an application.
2. Add a Web redirect URI: `http://localhost:5000/auth/authorized` (or your production URL).
3. Create a client secret.
4. Grant delegated permission `User.Read` (Microsoft Graph).

## Auth Policy Configuration

`extra.auth` in `mkdocs.yml` is optional. If it is omitted entirely, the app still works with these defaults:

- authentication enabled
- no domain allow-list
- no email allow-list

Add this section only when you want to override the defaults:

```yaml
extra:
  auth:
    enabled: true
    allowed_domains: []
    allowed_emails: []
```

Behavior:

- If `extra.auth` is missing, MSAL authentication still applies with default behavior.
- If both lists are empty, any successfully authenticated Entra user is allowed.
- If either list is populated, user must match one of the configured domains or emails.

## Docker

```bash
docker build -t mkdocs-msal-auth .
docker run -p 5000:5000 \
  -e CLIENT_ID="your-client-id" \
  -e CLIENT_SECRET="your-client-secret" \
  -e TENANT_ID="your-tenant-id" \
  -e SECRET_KEY="your-secret-key" \
  -e SESSION_COOKIE_SECURE=true \
  mkdocs-msal-auth
```

## Smoke Check

Run:

```bash
python3 scripts/smoke_token.py
```

This verifies required Entra-related environment variables are present and prints the resolved authority.

## Linting

Ruff is configured in `pyproject.toml`. Run lint checks for this repository with:

```bash
ruff check .
```

## Source Layout

- `src/webapp/server.py`: Flask application and Entra authentication flow
- `src/mkdocs_msal_auth/`: MkDocs hook package
- `wsgi.py`: production WSGI entrypoint
- `pyproject.toml`: project metadata plus Ruff and Google-style docstring settings

## License

MIT