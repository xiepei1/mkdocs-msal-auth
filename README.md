# MkDocs Google Authentication

This project integrates Google OAuth authentication with MkDocs, allowing you to secure your documentation site with Google login.

## Features

- Secure documentation with Google OAuth
- Restrict access to specific domains
- Restrict access to specific email addresses
- Simple integration with MkDocs

## Quick Start

1. Clone this repository
2. Install the requirements: `pip install -r requirements.txt`
3. Set up your Google OAuth credentials in the Google Cloud Console
4. Set environment variables for your credentials:
   ```
   export GOOGLE_CLIENT_ID="your_client_id"
   export GOOGLE_CLIENT_SECRET="your_client_secret"
   export SECRET_KEY="your_secret_key"
   ```
5. Build the MkDocs site: `mkdocs build`
6. Run the server: `python server.py`

## Configuration

Edit the `mkdocs.yml` file to configure authentication:

```yaml
extra:
  auth:
    enabled: true
    allowed_domains:
      - yourdomain.com
    allowed_emails:
      - specific.user@gmail.com
```

## Deployment

See the `.github/workflows/deploy.yml` file for an example GitHub Actions workflow for deployment.

## Authentication (MSAL / Azure AD)

This project was migrated from a Google OAuth implementation to use MSAL (Azure AD)
for SSO. The server issues short-lived signed tokens that are stored by the browser
in localStorage and sent as a Bearer token to the server for verification.

For local development copy `.env.example` to `.env` and populate the values:

```
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
TENANT_ID=your-tenant-id
SECRET_KEY=a-very-secret-key
```

To run a quick smoke verification of the token helpers:

```bash
python3 scripts/smoke_token.py
```

If you'd prefer token validation against Azure AD (JWT validation using JWKS),
I can add that alternative flow; currently the server uses itsdangerous-signed
tokens for fast server-side verification without needing to validate external
JWTs on every request.

## License

MIT