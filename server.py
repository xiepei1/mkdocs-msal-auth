#!/usr/bin/env python3
"""Server implementation using MSAL (Azure AD) for MkDocs SSO.

This replaces the previous Google OAuth implementation. Environment variables
CLIENT_ID, CLIENT_SECRET, TENANT_ID, and AUTHORITY (optional) are read via
python-dotenv or the environment at runtime.
"""

import os
import logging
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    redirect,
    request,
    session,
    url_for,
    jsonify,
    send_from_directory,
)

from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
import msal
import requests

# Load environment from .env if present
load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# App configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# MSAL / Azure AD configuration (passed in at runtime via environment)
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
TENANT_ID = os.environ.get('TENANT_ID')
AUTHORITY = os.environ.get('AUTHORITY') or (f"https://login.microsoftonline.com/{TENANT_ID}" if TENANT_ID else None)

# Auth config: defaults; may be overridden by mkdocs.yml extra.auth
AUTH_ENABLED = True
ALLOWED_DOMAINS = ['gmail.com']
ALLOWED_EMAILS = []

# Attempt to read mkdocs.yml for extra auth config
try:
    import yaml

    with open('mkdocs.yml', 'r') as f:
        mkdocs_config = yaml.safe_load(f)
        auth_config = mkdocs_config.get('extra', {}).get('auth', {})

        if auth_config:
            AUTH_ENABLED = auth_config.get('enabled', True)
            ALLOWED_DOMAINS = auth_config.get('allowed_domains', ALLOWED_DOMAINS)
            ALLOWED_EMAILS = auth_config.get('allowed_emails', ALLOWED_EMAILS)
except Exception:
    # Non-fatal; keep defaults
    pass

# Create MSAL confidential client application when config is present
CLIENT_APP = None
if CLIENT_ID and CLIENT_SECRET and AUTHORITY:
    CLIENT_APP = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )
else:
    app.logger.warning('MSAL not fully configured. Set CLIENT_ID, CLIENT_SECRET, and TENANT_ID/AUTHORITY.')

# Paths exempt from authentication when serving the built site
AUTH_PATHS_EXEMPT = ['/login/', '/auth/', '/assets/', '/javascripts/', '/stylesheets/']

# Scopes requested from Microsoft Identity platform
SCOPES = ['User.Read', 'openid', 'profile', 'email']


@app.route('/auth/login')
def login():
    """Start the authorization flow by redirecting the user to Azure AD.

    This builds an authorization URL using MSAL and redirects the browser.
    """
    if not CLIENT_APP:
        return ("Authentication is not configured on the server."), 500

    redirect_uri = url_for('authorized', _external=True)
    auth_url = CLIENT_APP.get_authorization_request_url(scopes=SCOPES, redirect_uri=redirect_uri)
    return redirect(auth_url)


@app.route('/auth/authorized')
def authorized():
    """Callback endpoint for Azure AD to redirect to with authorization code."""
    if not CLIENT_APP:
        return ("Authentication is not configured on the server."), 500

    error = request.args.get('error')
    if error:
        return redirect(f"/login?error={error}")

    code = request.args.get('code')
    if not code:
        return redirect('/login?error=no_code')

    redirect_uri = url_for('authorized', _external=True)
    result = CLIENT_APP.acquire_token_by_authorization_code(code, scopes=SCOPES, redirect_uri=redirect_uri)

    if 'access_token' in result:
        # Try to extract a user identifier from the id token claims
        claims = result.get('id_token_claims', {})
        email = claims.get('email') or claims.get('preferred_username') or claims.get('upn')

        # Fallback: attempt to call Graph for user profile
        if not email:
            try:
                graph_resp = requests.get(
                    'https://graph.microsoft.com/v1.0/me',
                    headers={'Authorization': f"Bearer {result['access_token']}"},
                    timeout=5,
                )
                if graph_resp.ok:
                    graph_data = graph_resp.json()
                    email = graph_data.get('mail') or graph_data.get('userPrincipalName')
            except Exception:
                pass

        if not email:
            return redirect('/login?error=no_email')

        # domain/email checks
        domain = email.split('@')[-1]
        allowed_domain_ok = (not ALLOWED_DOMAINS) or (domain in ALLOWED_DOMAINS)
        allowed_email_ok = (not ALLOWED_EMAILS) or (email in ALLOWED_EMAILS)

        if allowed_domain_ok or allowed_email_ok:
            # Set the user identifier in the secure Flask session
            session['user'] = email
            
            # Redirect to the main site 
            return redirect('/')

    # Authentication failed
    return redirect('/login?error=unauthorized')


@app.route('/auth/verify', methods=['POST'])
def verify_token():
    """Endpoint for frontend JS to verify authentication status if needed."""
    if 'user' in session:
        return jsonify({'valid': True, 'email': session['user']})
    
    return jsonify({'valid': False, 'error': 'Unauthorized'}), 401


@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect('/login')


# Serve the built mkdocs site
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_site(path):
    site_dir = Path('site')
    # Authentication guard for site content
    from flask import request, redirect

    request_path = request.path
    for exempt in AUTH_PATHS_EXEMPT:
        if request_path.startswith(exempt):
            break
    else:
        # Not exempt: check the Flask session
        if 'user' not in session:
            return redirect('/auth/login')

    requested_path = site_dir / path
    if not requested_path.exists():
        if (site_dir / f"{path}.html").exists():
            path = f"{path}.html"
        elif (site_dir / path / "index.html").exists():
            path = f"{path}/index.html"

    return send_from_directory('site', path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)