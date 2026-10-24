# Docs + Flask + Microsoft Entra ID Authentication

This project builds documentation with [MkDocs](https://www.mkdocs.org/) and
the [Material](https://squidfunk.github.io/mkdocs-material/) theme.
It serves the generated static site through Flask. Access is protected with
Microsoft Entra ID (Azure AD) through MSAL for Python.

## Architecture

1. MkDocs builds static HTML into the `site/` folder.
2. Flask serves files from `site/`.
3. Unauthenticated users are redirected to Microsoft Entra ID login.
4. After successful sign-in, Flask stores the user identity in a secure session.
5. Optionally restrict access by email domain and by specific email addresses.

## Features

- Documentation generation with MkDocs and the Material theme
- Flask server for hosting generated HTML
- Microsoft Entra ID OAuth2 authorization code flow via MSAL
- Access control using `allowed_domains` and `allowed_emails`
- Runtime config from environment variables (`.env` for local development)

## Quick Start

Dependencies are managed with [uv](https://docs.astral.sh/uv/).

1. Install dependencies:

```bash
uv sync
```

2. Copy environment template and fill values:

```bash
cp .env.example .env
```

3. Build docs:

```bash
uv run mkdocs build
```

4. Start local server:

```bash
uv run python -m src.webapp.server
```

5. Open `http://localhost:5000`.

## Development

```bash
uv run pytest            # run the test suite
uv run ruff check .      # lint
uv run mkdocs serve      # live docs preview
```

The test suite needs no Entra ID credentials and makes no network calls. It
covers the auth allow-list, the exempt-path rules, config loading, and every
branch of the login and callback flow.

`pyproject.toml` is the source of truth for dependencies and `uv.lock` pins
exact versions. Run `uv sync` after pulling changes. Add a dependency with
`uv add <package>` and a development tool with `uv add --dev <package>`.

## Production Run (WSGI)

Use Gunicorn with the WSGI entrypoint:

```bash
.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 src.webapp.wsgi:app
```

Optional hardening:

- When you serve over HTTPS, set `SESSION_COOKIE_SECURE=true`.
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

## Auth Policy Config

`extra.auth` in `mkdocs.yml` is optional. If it is omitted entirely, the app still works with these defaults:

- authentication enabled
- no domain allow-list
- no email allow-list

Add this section to override the defaults:

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
- If either list is populated, user must match one of the allowed domains or emails.

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

The image installs dependencies from `uv.lock` and builds the docs site at
image build time.

## Smoke Check

Run:

```bash
python3 scripts/smoke_token.py
```

This checks that the required Entra-related environment variables are present
and prints the resolved authority. It is the one check that needs real
credentials.

## Source Layout

```
.
├── .claude/settings.json       agent command allow list
├── .github/
│   ├── instructions/           pointer to AGENTS.md
│   └── workflows/ci.yml        lint, test, and build on every push
├── docs/                       Markdown that MkDocs builds
│   ├── assets/                 login page styles and error script
│   ├── index.md
│   ├── login.md
│   └── setup.md
├── scripts/
│   └── smoke_token.py          reads env vars and prints the authority
├── src/
│   ├── mkdocs_msal_auth/
│   │   └── hooks.py            MkDocs build hooks for auth settings
│   └── webapp/
│       ├── server.py           Flask app and Entra auth flow
│       └── wsgi.py             production WSGI entrypoint
├── tests/                      pytest suite, no network and no credentials
│   ├── conftest.py             fixtures and fakes at the MSAL and Graph edge
│   ├── test_auth_policy.py     allow-list and exempt-path rules
│   ├── test_config.py          env and mkdocs.yml loading
│   ├── test_hooks.py           MkDocs build hook contracts
│   └── test_routes.py          login, callback, logout, and static serving
├── AGENTS.md                   agent guidance, the single source of truth
├── CLAUDE.md                   pointer to AGENTS.md
├── Dockerfile                  builds site/ then serves it with Gunicorn
├── mkdocs.yml                  MkDocs config and the extra.auth policy
├── pyproject.toml              dependencies and tool config
└── .python-version             pinned Python version
```

The Flask app lives under `src/webapp/`. The MkDocs build hooks live
under `src/mkdocs_msal_auth/`. Docs content lives under `docs/`. Tests
live under `tests/` and never touch the network. Files under `.cache/`,
`.pytest_cache/`, `.ruff_cache/`, `site/`, and `.venv/` are generated and
are not tracked by git.

## License

MIT
