"""Access-policy tests for the auth allow-list and exempt-path rules.

Each case names the production change it catches. Expectations are
hand-derived literals so nothing is computed by the code under test.
"""

import pytest


@pytest.mark.parametrize(
    ('email', 'allowed_domains', 'allowed_emails', 'expected'),
    [
        # Both lists empty: every authenticated user is allowed.
        ('anyone@example.com', [], [], True),
        # Exact email allow-list hit, even outside an allowed domain.
        ('contractor@vendor.io', ['example.com'], ['contractor@vendor.io'], True),
        # Domain allow-list hit.
        ('dev@example.com', ['example.com'], [], True),
        # Domain comparison is case-insensitive on both sides.
        ('dev@EXAMPLE.com', ['Example.COM'], [], True),
        # On neither list: denied.
        ('intruder@evil.com', ['example.com'], ['dev@example.com'], False),
        # A look-alike suffix must not satisfy an exact domain match.
        ('dev@evil-example.com', ['example.com'], [], False),
    ],
)
def test_is_email_allowed(
    server, monkeypatch, email, allowed_domains, allowed_emails, expected
):
    """Allow-list enforcement decides access from domain and email lists."""
    monkeypatch.setattr(server, 'ALLOWED_DOMAINS', allowed_domains)
    monkeypatch.setattr(server, 'ALLOWED_EMAILS', allowed_emails)

    assert server._is_email_allowed(email) is expected


@pytest.mark.parametrize(
    ('path', 'expected'),
    [
        # Auth routes must stay reachable without a session.
        ('/auth/login', True),
        ('/auth/authorized', True),
        ('/auth/verify', True),
        ('/auth/logout', True),
        ('/login/', True),
        # Static assets the login page needs must stay reachable.
        ('/assets/app.css', True),
        ('/javascripts/bundle.js', True),
        ('/stylesheets/extra.css', True),
        ('/images/logo.png', True),
        # Documentation pages must stay behind the auth gate.
        ('/', False),
        ('/index.html', False),
        ('/setup/', False),
        ('/setup/index.html', False),
    ],
)
def test_is_exempt_path(server, path, expected):
    """Only auth routes and static assets bypass the auth gate."""
    assert server._is_exempt_path(path) is expected
