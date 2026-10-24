# Setup Guide

## Prerequisites

- Python 3.12 (pinned in `.python-version`)
- [uv](https://docs.astral.sh/uv/) for dependency management
- Microsoft Entra tenant (Azure AD)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/mkdocs-msal-auth.git
cd mkdocs-msal-auth
```

2. Install the locked dependencies:

```bash
uv sync
```

This creates `.venv` and installs both runtime and development dependencies
from `uv.lock`. Run it again after every pull.

## Microsoft Entra ID Setup

1. Open [Microsoft Entra admin center](https://entra.microsoft.com/).
2. Register a new application.
3. In Authentication, add a Web redirect URI:
   - Local: `http://localhost:5000/auth/authorized`
   - Production: `https://yourdocs.example.com/auth/authorized`
4. In Certificates & secrets, create a client secret.
5. In API permissions, remove the `User.Read` entry. The app signs users
   in with OpenID Connect and reads the email claim. It does not call
   Microsoft Graph.
6. Capture these values:
   - Application (client) ID
   - Directory (tenant) ID
   - Client secret

## Config

1. Create environment variables for Entra credentials:

```bash
cp .env.example .env
```

Example `.env` values:

```env
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
TENANT_ID=your-tenant-id
SECRET_KEY=random_secure_secret_key
```

2. `mkdocs.yml` does not need an `extra.auth` section for MSAL authentication to work. If omitted, the app defaults to enabled auth with no domain or email restrictions.

Add `extra.auth` to override that behavior:

```yaml
extra:
  auth:
    enabled: true
    allowed_domains: []
    allowed_emails: []
```

Notes:

- Omitting `extra.auth` entirely is valid.
- Leave both lists empty to allow any authenticated Entra account.
- Populate one or both lists to enforce allow-lists.

## Local Development

```bash
# Build the docs site
uv run mkdocs build

# Run the server
uv run python -m app.webapp.server
```

The server runs on http://localhost:5000 by default.

## Project Layout

```
.
├── app/                    all Python code
│   ├── mkdocs_msal_auth/
│   │   └── hooks.py        MkDocs build hooks for auth settings
│   └── webapp/
│       ├── server.py       Flask app and Entra auth flow
│       └── wsgi.py         production WSGI entrypoint
├── docs/                   Markdown that MkDocs builds
│   └── assets/             login page styles and error script
├── tests/                  pytest suite, no network and no credentials
├── AGENTS.md               agent guidance, the single source of truth
├── Dockerfile              builds site/ then serves it with Gunicorn
├── mkdocs.yml              MkDocs config and the extra.auth policy
└── pyproject.toml          dependencies and tool config
```

Change auth behavior in `app/webapp/server.py`. Change the allow-lists
in the `extra.auth` section of `mkdocs.yml`. Change dependencies in
`pyproject.toml`, then run `uv sync`.

For production, use Gunicorn from the project virtualenv:

```bash
.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 app.webapp.wsgi:app
```

## Deployment

You can deploy this site to any platform that supports Python applications.

### 1. Use Docker

The repository includes a Dockerfile. It installs from `uv.lock` and builds
the docs site at image build time.

```bash
# Build the Docker image
docker build -t mkdocs-msal-auth .

# Run the container
docker run -p 5000:5000 \
  -e CLIENT_ID="your-client-id" \
  -e CLIENT_SECRET="your-client-secret" \
  -e TENANT_ID="your-tenant-id" \
  -e SECRET_KEY="your-secret-key" \
  -e SESSION_COOKIE_SECURE=true \
  mkdocs-msal-auth
```

### 2. Deploy to a Python host

Any platform that can run a WSGI server works. It needs to:

1. Run `uv sync --frozen --no-dev` to install production dependencies.
2. Run `uv run mkdocs build` to generate `site/`.
3. Start Gunicorn on `app.webapp.wsgi:app`.

Pass the same environment variables listed above as platform secrets.

### 3. Host the static site separately

You can publish the static `site/` folder to a static host and run the
authentication server somewhere else. Route your domain so that auth
requests reach the Flask server. This repo does not ship a deploy workflow
for that layout, so wire it up in your own CI.
