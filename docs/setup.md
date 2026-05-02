# Setup Guide

## Prerequisites

- Python 3.9+
- MkDocs
- MkDocs Material theme
- Microsoft Entra tenant (Azure AD)

## Installation

1. Install required packages:

```bash
pip install -r requirements.txt
```

Optional for editable local development:

```bash
pip install -e .
```

2. Clone this repository:

```bash
git clone https://github.com/yourusername/mkdocs-msal-auth.git
cd mkdocs-msal-auth
```

## Microsoft Entra ID Setup

1. Open [Microsoft Entra admin center](https://entra.microsoft.com/).
2. Register a new application.
3. In Authentication, add a Web redirect URI:
  - Local: `http://localhost:5000/auth/authorized`
  - Production: `https://yourdocs.example.com/auth/authorized`
4. In Certificates & secrets, create a client secret.
5. In API permissions, add delegated permission `User.Read` for Microsoft Graph.
6. Capture these values:
  - Application (client) ID
  - Directory (tenant) ID
  - Client secret

## Configuration

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

Add `extra.auth` only if you want to override that behavior:

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

## Deployment

You can deploy this site to any platform that supports Python applications. Some common options are:

### 1. Use Docker

The repository includes a Dockerfile for easy containerization:

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

### 2. Deploy to Heroku

```bash
# Install Heroku CLI
heroku create your-mkdocs-site
heroku config:set CLIENT_ID="your-client-id"
heroku config:set CLIENT_SECRET="your-client-secret"
heroku config:set TENANT_ID="your-tenant-id"
heroku config:set SECRET_KEY="your-secret-key"
git push heroku master
```

### 3. Deploy to GitHub Pages with a Separate Authentication Server

You can also deploy the static MkDocs site to GitHub Pages and run the authentication server separately:

1. Use GitHub Actions to build and deploy the static site (see `.github/workflows/deploy.yml`)
2. Run the authentication server on a separate platform (e.g., Heroku, Digital Ocean)
3. Configure your domain to route authentication requests to the server

## Local Development

For local development, you can run:

```bash
# Build the MkDocs site
mkdocs build

# Optional sanity check for env config
python scripts/smoke_token.py

# Run the server
python -m src.webapp.server
```

The server will run on http://localhost:5000 by default.

For production, use Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 3 wsgi:app
```