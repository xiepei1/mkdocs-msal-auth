"""Fixtures for the auth test suite.

The Flask app is exercised exactly as it runs in production: no app
factory and no product-code changes. Module globals are monkeypatched
per test instead, so the suite needs no Entra ID credentials and makes
no network calls.
"""

import importlib

import pytest


@pytest.fixture(scope='session')
def server():
    """Import the auth module once under a controlled environment.

    ``CLIENT_ID``/``CLIENT_SECRET``/``TENANT_ID`` stay unset so import
    leaves ``CLIENT_APP`` as ``None``; tests that need MSAL inject a fake
    client explicitly.
    """
    return importlib.import_module('src.webapp.server')


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
    boundary. ``get_authorization_request_url`` echoes the redirect URI
    it was given into the returned URL, so tests can assert the redirect
    the browser actually receives rather than asserting on the double.
    """

    def __init__(self, token_result=None):
        """Record the token result to hand back and any token calls made.

        Args:
            token_result: Mapping to return from the token exchange.
        """
        self.token_result = token_result or {}
        self.token_calls = []

    def get_authorization_request_url(self, scopes, redirect_uri):
        """Build a fake authorize URL echoing the redirect URI received.

        Args:
            scopes: Scopes the caller wants authorized.
            redirect_uri: Callback URL the caller registered.

        Returns:
            A URL string the test can assert against.
        """
        return (
            'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            f'?redirect_uri={redirect_uri}'
            f'&scope={" ".join(scopes)}'
        )

    def acquire_token_by_authorization_code(self, code, scopes, redirect_uri):
        """Pretend to exchange an authorization code for a token.

        Args:
            code: Authorization code from the callback query string.
            scopes: Scopes to request.
            redirect_uri: Callback URL, which must match the authorize step.

        Returns:
            The configured token result mapping.
        """
        self.token_calls.append(
            {
                'code': code,
                'scopes': scopes,
                'redirect_uri': redirect_uri,
            }
        )
        return self.token_result


class FakeGraphResponse:
    """Stand-in for a ``requests`` response from Microsoft Graph."""

    def __init__(self, payload=None, ok=True):
        """Set the JSON payload and the response status flag.

        Args:
            payload: Mapping to return from ``json()``.
            ok: Whether the response counts as successful.
        """
        self._payload = payload if payload is not None else {}
        self.ok = ok

    def json(self):
        """Return the configured JSON payload.

        Returns:
            The payload mapping.
        """
        return self._payload


class FakeRequests:
    """Replace ``requests`` on the server module for one test.

    Scoped to the module under test so the real ``requests`` package
    keeps working everywhere else.
    """

    def __init__(self, response):
        """Hold the response to return and record every call made.

        Args:
            response: Object to return from ``get()``.
        """
        self._response = response
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        """Return the canned response and record the request made.

        Args:
            url: Requested URL.
            headers: Request headers sent.
            timeout: Timeout in seconds the caller allowed.

        Returns:
            The canned response object.
        """
        self.calls.append({'url': url, 'headers': headers, 'timeout': timeout})
        return self._response


@pytest.fixture
def fake_msal(server, monkeypatch):
    """Install a fake MSAL client and hand it back for configuration."""

    def install(token_result=None):
        app = FakeMsalApp(token_result=token_result)
        monkeypatch.setattr(server, 'CLIENT_APP', app)
        return app

    return install


@pytest.fixture
def fake_graph(server, monkeypatch):
    """Install a fake Graph HTTP client returning ``payload`` as JSON."""

    def install(payload=None, ok=True):
        fake = FakeRequests(FakeGraphResponse(payload, ok=ok))
        monkeypatch.setattr(server, 'requests', fake)
        return fake

    return install
