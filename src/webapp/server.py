#!/usr/bin/env python3
"""Flask host for MkDocs static site with Microsoft Entra ID authentication."""

import os
from pathlib import Path
from typing import Any

import msal
import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

# Load environment from .env if present
load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT_DIR / 'site'
MKDOCS_CONFIG_PATH = ROOT_DIR / 'mkdocs.yml'


def _env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean value parsed from an environment variable.

    Args:
        name: Environment variable name to read.
        default: Value to return when the variable is missing.

    Returns:
        Parsed boolean value.
    """
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = _env_bool('SESSION_COOKIE_SECURE', default=False)

if app.secret_key == 'dev-secret-key':
    app.logger.warning(
        'Using default SECRET_KEY. Set SECRET_KEY in environment '
        'for non-development use.'
    )

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
TENANT_ID = os.environ.get('TENANT_ID')
AUTHORITY = os.environ.get('AUTHORITY') or (
    f"https://login.microsoftonline.com/{TENANT_ID}" if TENANT_ID else None
)

AUTH_ENABLED = True
ALLOWED_DOMAINS = []
ALLOWED_EMAILS = []


def _default_auth_config() -> dict[str, Any]:
    """Return the default authentication configuration.

    Returns:
        Default auth settings used when ``extra.auth`` is not defined.
    """
    return {
        'enabled': True,
        'allowed_domains': [],
        'allowed_emails': [],
    }


def _load_auth_config_from_mkdocs() -> None:
    """Load auth settings from ``mkdocs.yml`` when present.

    The function keeps the current values when the config file, the YAML
    parser, or the ``extra.auth`` section is unavailable or malformed.
    """
    global AUTH_ENABLED, ALLOWED_DOMAINS, ALLOWED_EMAILS

    if not yaml:
        return

    try:
        with open(MKDOCS_CONFIG_PATH, 'r', encoding='utf-8') as file:
            mkdocs_config = yaml.safe_load(file) or {}
    except Exception:
        return

    auth_config = _default_auth_config()
    extra = mkdocs_config.get('extra')
    auth_section = extra.get('auth') if isinstance(extra, dict) else None
    # A bare `extra:`, or an `auth:` holding a scalar, parses to None or a
    # non-mapping. Treat either as "no override" so a partially edited
    # mkdocs.yml cannot stop the process from importing.
    if isinstance(auth_section, dict):
        auth_config.update(auth_section)
    AUTH_ENABLED = bool(auth_config['enabled'])
    ALLOWED_DOMAINS = auth_config['allowed_domains'] or []
    ALLOWED_EMAILS = auth_config['allowed_emails'] or []


_load_auth_config_from_mkdocs()

CLIENT_APP = None
if CLIENT_ID and CLIENT_SECRET and AUTHORITY:
    CLIENT_APP = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )
else:
    app.logger.warning(
        'MSAL not fully configured. Set CLIENT_ID, CLIENT_SECRET, '
        'and TENANT_ID/AUTHORITY.'
    )

AUTH_PATHS_EXEMPT = [
    '/auth',
    '/login',
    '/assets/',
    '/javascripts/',
    '/stylesheets/',
    '/images/',
]

# Scopes requested from Microsoft Identity platform
SCOPES = ['openid', 'profile', 'email', 'User.Read']


def _is_email_allowed(email: str) -> bool:
    """Return whether the authenticated email passes allow-list checks.

    Args:
        email: User email resolved from Entra ID or Microsoft Graph.

    Returns:
        ``True`` when access should be granted.
    """
    if not ALLOWED_DOMAINS and not ALLOWED_EMAILS:
        return True

    if email in ALLOWED_EMAILS:
        return True

    domain = email.split('@')[-1].lower()
    return domain in {item.lower() for item in ALLOWED_DOMAINS}


def _is_exempt_path(path: str) -> bool:
    """Return whether a request path bypasses authentication.

    Args:
        path: Request path being evaluated.

    Returns:
        ``True`` when the path is exempt from auth checks.
    """
    return any(path.startswith(prefix) for prefix in AUTH_PATHS_EXEMPT)


@app.route('/auth/login')
def login():
    """Start Entra ID authorization by redirecting to Microsoft login."""
    if not AUTH_ENABLED:
        return redirect('/')

    if not CLIENT_APP:
        return ('Authentication is not configured on the server.'), 500

    redirect_uri = url_for('authorized', _external=True)
    auth_url = CLIENT_APP.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    return redirect(auth_url)


@app.route('/auth/authorized')
def authorized():
    """Handle the Entra ID authorization callback."""
    if not AUTH_ENABLED:
        return redirect('/')

    if not CLIENT_APP:
        return ('Authentication is not configured on the server.'), 500

    error = request.args.get('error')
    if error:
        return redirect(f"/login/?error={error}")

    code = request.args.get('code')
    if not code:
        return redirect('/login/?error=no_code')

    redirect_uri = url_for('authorized', _external=True)
    result = CLIENT_APP.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    if 'access_token' in result:
        # Try to extract a user identifier from the id token claims
        claims = result.get('id_token_claims', {})
        email = (
            claims.get('email')
            or claims.get('preferred_username')
            or claims.get('upn')
        )

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
                    email = graph_data.get('mail') or graph_data.get(
                        'userPrincipalName'
                    )
            except Exception:
                pass

        if not email:
            return redirect('/login/?error=no_email')

        if _is_email_allowed(email):
            session['user'] = email
            return redirect('/')

    return redirect('/login/?error=unauthorized')


@app.route('/auth/verify', methods=['POST'])
def verify_token():
    """Return current auth status for diagnostics."""
    if not AUTH_ENABLED:
        return jsonify({'valid': True, 'email': None, 'auth_enabled': False})

    if 'user' in session:
        return jsonify(
            {'valid': True, 'email': session['user'], 'auth_enabled': True}
        )

    return (
        jsonify({'valid': False, 'error': 'Unauthorized', 'auth_enabled': True}),
        401,
    )


@app.route('/auth/logout')
def logout():
    """Clear the current session and return to the login page."""
    session.clear()
    return redirect('/login/')


@app.route('/login')
@app.route('/login/')
def login_page():
    """Serve the static login page generated by MkDocs."""
    login_index = SITE_DIR / 'login' / 'index.html'
    if login_index.exists():
        return send_from_directory(SITE_DIR, 'login/index.html')
    return redirect('/auth/login')


# Serve the built mkdocs site
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_site(path):
    """Serve generated MkDocs files with session-based access control.

    Args:
        path: Requested path inside the generated ``site`` directory.

    Returns:
        Flask response for the requested file or a redirect to login.
    """
    if AUTH_ENABLED and not _is_exempt_path(request.path) and 'user' not in session:
        return redirect('/auth/login')

    requested_path = SITE_DIR / path
    # A directory is not a servable file. MkDocs emits directory URLs
    # (setup/index.html served at /setup/), so fall through to the
    # index.html resolution instead of handing the directory to
    # send_from_directory.
    if not requested_path.exists() or requested_path.is_dir():
        if (SITE_DIR / f"{path}.html").exists():
            path = f"{path}.html"
        else:
            index_candidate = f"{path.rstrip('/')}/index.html"
            if (SITE_DIR / index_candidate).exists():
                path = index_candidate

    if (SITE_DIR / path).is_file():
        return send_from_directory(SITE_DIR, path)

    # MkDocs writes site/404.html on every build. Serve that page for a
    # path with no generated file so the site's own not-found page is used
    # instead of the bare Flask error.
    if (SITE_DIR / '404.html').is_file():
        return send_from_directory(SITE_DIR, '404.html'), 404

    abort(404)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=_env_bool('FLASK_DEBUG', default=False),
    )
