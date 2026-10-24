"""Route-level tests for the Flask auth flow.

MSAL and Microsoft Graph are replaced at their network boundary. The
assertions target what the app returns to the client, not the doubles.
"""


def test_unauthenticated_root_redirects_to_login(client):
    """An anonymous request for the docs root is sent to login."""
    response = client.get('/')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_unauthenticated_protected_page_redirects_to_login(client):
    """Auth gating applies to nested pages, not just the root."""
    response = client.get('/setup/')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_exempt_asset_is_served_without_session(client):
    """Login-page assets stay reachable so the login page can render."""
    response = client.get('/assets/app.css')

    assert response.status_code == 200
    assert b'body' in response.data


def test_traversal_under_exempt_prefix_does_not_bypass_auth(client):
    """A `..` path under /assets/ must not serve docs anonymously.

    Regression: the gate matched raw prefixes on the un-normalized path,
    so `/assets/../setup/index.html` counted as an asset and the
    protected page came back with no session at all.
    """
    response = client.get('/assets/../setup/index.html')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_traversal_under_exempt_prefix_serves_content_when_signed_in(
    signed_in,
):
    """After the gate, the same path is just the page it resolves to.

    Normalizing must not deny a signed-in reader a page that exists.
    """
    response = signed_in.get('/assets/../setup/index.html')

    assert response.status_code == 200
    assert b'setup guide' in response.data


def test_look_alike_prefix_does_not_bypass_auth(client):
    """A name that merely starts like an exempt route stays protected."""
    for path in ('/authorize/', '/login-spoof/', '/assets-backup/x.html'):
        response = client.get(path)

        assert response.status_code == 302, path
        assert response.headers['Location'].endswith('/auth/login'), path


def test_authenticated_request_serves_content(signed_in):
    """A signed-in user receives the generated docs content."""
    response = signed_in.get('/')

    assert response.status_code == 200
    assert b'docs home' in response.data


def test_directory_url_resolves_to_index(signed_in):
    """A directory URL serves the page MkDocs generated for it.

    Catches the fallback skipping index.html whenever the directory
    itself exists, which is exactly the MkDocs directory-URL layout.
    """
    for path in ('/setup/', '/setup'):
        response = signed_in.get(path)

        assert response.status_code == 200, path
        assert b'setup guide' in response.data, path


def test_missing_page_serves_the_built_404_page(signed_in, site_dir):
    """A path with no generated file returns the site's own 404 page.

    MkDocs writes site/404.html on every build. Handing that page back
    is the point of generating it.
    """
    (site_dir / '404.html').write_text(
        '<h1>page not found</h1>', encoding='utf-8'
    )

    response = signed_in.get('/no-such-page/')

    assert response.status_code == 404
    assert b'page not found' in response.data


def test_missing_page_without_built_404_still_returns_404(signed_in):
    """With no 404 page generated the client still gets a 404 status."""
    response = signed_in.get('/no-such-page/')

    assert response.status_code == 404


def test_verify_reports_authenticated_user(signed_in):
    """/auth/verify echoes the signed-in identity."""
    response = signed_in.post('/auth/verify')

    assert response.status_code == 200
    assert response.get_json() == {
        'valid': True,
        'email': 'dev@example.com',
        'auth_enabled': True,
    }


def test_verify_rejects_unauthenticated(client):
    """/auth/verify reports 401 when there is no session."""
    response = client.post('/auth/verify')

    assert response.status_code == 401
    assert response.get_json()['valid'] is False


def test_verify_when_auth_disabled(client, server, monkeypatch):
    """With auth disabled, /auth/verify reports the gate as off."""
    monkeypatch.setattr(server, 'AUTH_ENABLED', False)

    response = client.post('/auth/verify')

    assert response.status_code == 200
    assert response.get_json() == {
        'valid': True,
        'email': None,
        'auth_enabled': False,
    }


def test_logout_clears_session(signed_in):
    """Logging out drops the session so the next request is anonymous."""
    response = signed_in.get('/auth/logout')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login/')
    assert signed_in.post('/auth/verify').status_code == 401


def test_login_redirects_to_authority(client, server, fake_msal):
    """Login sends the browser to Entra with the expected scopes."""
    fake_msal()

    response = client.get('/auth/login')

    assert response.status_code == 302
    location = response.headers['Location']
    assert location.startswith('https://login.microsoftonline.com/')
    # The redirect URI is production's contract with Entra; it must be the
    # absolute callback URL or the token exchange cannot complete.
    assert 'redirect_uri=http://localhost/auth/authorized' in location
    # The app asks for the application scopes it needs. MSAL appends the
    # reserved OIDC scopes to whatever travels on the wire.
    assert 'email' in location
    assert 'User.Read' in location


def test_scopes_omit_msal_reserved_values(server):
    """The requested scopes must not carry values MSAL reserves.

    ``msal.application.ClientApplication._decorate_scope`` adds
    ``openid``, ``profile`` and ``offline_access`` on its own and raises
    ``ValueError`` when the caller passes any of them. With those values
    in ``SCOPES``, every call to ``/auth/login`` and
    ``/auth/authorized`` 500s against a real MSAL client, so the sign-in
    flow never worked. The fake refuses them too, so this stays fixed.
    """
    reserved = frozenset(['openid', 'profile', 'offline_access'])

    assert not reserved & set(server.SCOPES)
    # The allow-list check reads the email claim, so ask for it.
    assert 'email' in server.SCOPES


def test_authorized_survives_a_token_exchange_that_raises(client, fake_msal):
    """A token exchange that blows up must not surface as a 500.

    The code, the network, or Microsoft can fail between the redirect and
    the session. The caller is a browser mid-sign-in, so the only sane
    answer is the login page with a reason, never a raw server error.
    """
    fake = fake_msal()

    def explode(code, scopes, redirect_uri):
        raise RuntimeError('token endpoint unreachable')

    fake.acquire_token_by_authorization_code = explode

    response = client.get('/auth/authorized?code=abc')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login/?error=unauthorized')
    assert client.post('/auth/verify').status_code == 401


def test_login_unconfigured_returns_500(client):
    """Login fails loudly when MSAL credentials were never supplied."""
    response = client.get('/auth/login')

    assert response.status_code == 500
    assert b'not configured' in response.data


def test_login_when_auth_disabled_redirects_home(client, server, monkeypatch):
    """With auth disabled, /auth/login sends users straight to the docs."""
    monkeypatch.setattr(server, 'AUTH_ENABLED', False)

    response = client.get('/auth/login')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')


def test_authorized_forwards_provider_error(client, fake_msal):
    """A provider-side error is surfaced on the login page."""
    fake_msal()

    response = client.get('/auth/authorized?error=access_denied')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login/?error=access_denied')


def test_authorized_without_code_reports_no_code(client, fake_msal):
    """A callback missing the code parameter is treated as a failure."""
    fake_msal()

    response = client.get('/auth/authorized')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login/?error=no_code')


def test_authorized_success_sets_session(client, fake_msal):
    """An allowed identity from the token claims creates a session."""
    fake_msal(
        {
            'access_token': 'token-123',
            'id_token_claims': {'email': 'dev@example.com'},
        }
    )

    response = client.get('/auth/authorized?code=abc')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')
    assert client.post('/auth/verify').get_json()['email'] == 'dev@example.com'


def test_authorized_accepts_preferred_username(client, fake_msal):
    """preferred_username is accepted when the email claim is absent."""
    fake_msal(
        {
            'access_token': 'token-123',
            'id_token_claims': {'preferred_username': 'dev@example.com'},
        }
    )

    response = client.get('/auth/authorized?code=abc')

    assert response.status_code == 302
    assert client.post('/auth/verify').get_json()['email'] == 'dev@example.com'


def test_authorized_denied_by_allowlist_stays_logged_out(
    client, server, monkeypatch, fake_msal
):
    """An authenticated user outside the allow-list gets no session."""
    monkeypatch.setattr(server, 'ALLOWED_DOMAINS', ['example.com'])
    fake_msal(
        {
            'access_token': 'token-123',
            'id_token_claims': {'email': 'intruder@evil.com'},
        }
    )

    response = client.get('/auth/authorized?code=abc')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login/?error=unauthorized')
    assert client.post('/auth/verify').status_code == 401


def test_authorized_falls_back_to_graph_for_email(client, fake_msal, fake_graph):
    """When claims carry no email, the Graph profile supplies one."""
    fake_msal({'access_token': 'token-123', 'id_token_claims': {}})
    graph = fake_graph({'mail': 'dev@example.com'})

    response = client.get('/auth/authorized?code=abc')

    assert response.status_code == 302
    assert client.post('/auth/verify').get_json()['email'] == 'dev@example.com'
    assert graph.calls[0]['url'] == 'https://graph.microsoft.com/v1.0/me'


def test_authorized_without_any_email_reports_no_email(
    client, fake_msal, fake_graph
):
    """No email in claims or Graph means the identity cannot be checked."""
    fake_msal({'access_token': 'token-123', 'id_token_claims': {}})
    fake_graph({}, ok=False)

    response = client.get('/auth/authorized?code=abc')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login/?error=no_email')
    assert client.post('/auth/verify').status_code == 401


def test_authorized_token_failure_stays_logged_out(client, fake_msal):
    """A token response without an access token grants no session."""
    fake_msal({'error': 'invalid_grant'})

    response = client.get('/auth/authorized?code=abc')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login/?error=unauthorized')
    assert client.post('/auth/verify').status_code == 401
