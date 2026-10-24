"""Fixtures for the auth test suite.

The Flask app is exercised exactly as it runs in production: no app
factory and no product-code changes. Module globals are monkeypatched
per test instead, so the suite needs no Entra ID credentials and makes
no network calls.
"""

import importlib
import os

import pytest

# AGENTS.md declares SECRET_KEY required, and the server refuses to start
# without one because the key signs the session cookie that grants access.
# This is a throwaway test value, not a credential.
os.environ.setdefault('SECRET_KEY', 'test-only-session-signing-key')


@pytest.fixture(scope='session')
def server():
    """Import the auth module once under a controlled environment.

    ``CLIENT_ID``/``CLIENT_SECRET``/``TENANT_ID`` stay unset so import
    leaves ``CLIENT_APP`` as ``None``; tests that need MSAL inject a fake
    client explicitly.
    """
    return importlib.import_module('app.webapp.server')


@pytest.fixture(autouse=True)
def isolate_auth_state(server, monkeypatch):
    """Give every test a known auth policy and no MSAL client."""
    monkeypatch.setattr(server, 'AUTH_ENABLED', True)
    monkeypatch.setattr(server, 'ALLOWED_DOMAINS', [])
    monkeypatch.setattr(server, 'ALLOWED_EMAILS', [])
    monkeypatch.setattr(server, 'CLIENT_APP', None)


@pytest.fixture
def site_dir(server, tmp_path, monkeypatch):
    """Point the app at a throwaway site/ tree with known content."""
    site = tmp_path / 'site'
    (site / 'setup').mkdir(parents=True)
    (site / 'assets').mkdir()
    (site / 'index.html').write_text('<h1>docs home</h1>', encoding='utf-8')
    (site / 'setup' / 'index.html').write_text(
        '<h1>setup guide</h1>', encoding='utf-8'
    )
    (site / 'assets' / 'app.css').write_text('body {}', encoding='utf-8')
    monkeypatch.setattr(server, 'SITE_DIR', site)
    return site


@pytest.fixture
def client(server, site_dir):
    """Flask test client with a populated site directory."""
    server.app.config['TESTING'] = True
    return server.app.test_client()


@pytest.fixture
def signed_in(client):
    """Test client that already holds an authenticated session."""
    with client.session_transaction() as sess:
        sess['user'] = 'dev@example.com'
    return client


class FakeMsalApp:
    """Stand-in for ``msal.ConfidentialClientApplication``.

    The real client performs network I/O, so it is replaced at the MSAL
    boundary. Two behaviours of the real client are kept, because a
    double that drops them hides a login that cannot work.

    * ``get_authorization_request_url`` echoes the redirect URI it was
      given into the returned URL, so tests can assert the redirect the
      browser actually receives rather than asserting on the double.
    * Both entry points refuse the scopes MSAL reserves. See
      ``msal.application.ClientApplication._decorate_scope``: it adds
      ``openid``, ``profile`` and ``offline_access`` itself and raises
      ``ValueError`` when the caller passes any of them. A fake that
      accepts them let ``SCOPES`` carry reserved values straight
      through the suite while every real call 500s.
    """

    RESERVED_SCOPES = frozenset(['openid', 'profile', 'offline_access'])

    def __init__(self, token_result=None):
        """Record the token result to hand back and any token calls made.

        Args:
            token_result: Mapping to return from the token exchange.
        """
        self.token_result = token_result or {}
        self.token_calls = []
        self.requested_scopes = []

    def _decorate_scopes(self, scopes):
        """Return the scopes MSAL would put on the wire, or raise like it.

        Args:
            scopes: Scopes the caller asked for.

        Returns:
            The caller's scopes plus the reserved set MSAL adds.

        Raises:
            ValueError: If the caller passed a reserved scope.
        """
        self.requested_scopes = list(scopes)
        overlap = set(scopes) & self.RESERVED_SCOPES
        if overlap:
            raise ValueError(
                'You cannot use any scope value that is reserved: '
                f'{sorted(overlap)}'
            )
        return sorted(set(scopes) | self.RESERVED_SCOPES)

    def get_authorization_request_url(self, scopes, redirect_uri):
        """Build a fake authorize URL echoing the redirect URI received.

        Args:
            scopes: Scopes the caller wants authorized.
            redirect_uri: Callback URL the caller registered.

        Returns:
            A URL string the test can assert against.

        Raises:
            ValueError: If the caller passed a reserved scope.
        """
        decorated = self._decorate_scopes(scopes)
        return (
            'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            f'?redirect_uri={redirect_uri}'
            f'&scope={" ".join(decorated)}'
        )

    def acquire_token_by_authorization_code(self, code, scopes, redirect_uri):
        """Pretend to exchange an authorization code for a token.

        Args:
            code: Authorization code from the callback query string.
            scopes: Scopes to request.
            redirect_uri: Callback URL, which must match the authorize step.

        Returns:
            The configured token result mapping.

        Raises:
            ValueError: If the caller passed a reserved scope.
        """
        decorated = self._decorate_scopes(scopes)
        self.token_calls.append(
            {
                'code': code,
                'scopes': decorated,
                'redirect_uri': redirect_uri,
            }
        )
        return self.token_result


@pytest.fixture
def fake_msal(server, monkeypatch):
    """Install a fake MSAL client and hand it back for configuration."""

    def install(token_result=None):
        app = FakeMsalApp(token_result=token_result)
        monkeypatch.setattr(server, 'CLIENT_APP', app)
        return app

    return install
