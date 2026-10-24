"""Tests for the MkDocs build hooks.

These call the hooks with the exact argument shapes MkDocs 1.6.1 uses:
keyword-only ``config``, ``template_name``, ``page`` and ``files``. A
signature that only accepts them positionally raises ``TypeError`` at
build time, which is how the original module broke.
"""

import logging

import pytest

from app.mkdocs_msal_auth import hooks


@pytest.fixture(autouse=True)
def isolate_hook_state(monkeypatch):
    """Give every test a known auth policy for the hook module."""
    monkeypatch.setattr(hooks, 'AUTH_ENABLED', True)


def _config(extra):
    """Return the minimal config object the hooks read."""
    return {'extra': extra}


def test_on_pre_build_accepts_mkdocs_keyword_call():
    """MkDocs calls on_pre_build with config as a keyword-only argument."""
    result = hooks.on_pre_build(config=_config({'auth': {'enabled': False}}))

    assert result is None
    assert hooks.AUTH_ENABLED is False


def test_on_pre_build_survives_bare_extra_key():
    """A bare ``extra:`` parses to None and must not stop the build.

    Matches the contract in server.py: an unavailable section keeps the
    defaults rather than raising.
    """
    hooks.on_pre_build(config=_config(None))

    assert hooks.AUTH_ENABLED is True


def test_on_pre_build_survives_non_mapping_auth():
    """An ``extra.auth`` that is not a mapping is ignored, not raised."""
    hooks.on_pre_build(config=_config({'auth': True}))

    assert hooks.AUTH_ENABLED is True


def test_on_pre_build_never_logs_warnings(caplog, monkeypatch):
    """Building the docs must not need Entra credentials.

    MkDocs --strict turns log warnings into build errors. Warning here
    about missing credentials would make every secretless CI run fail,
    and the docs build does not use those credentials at all.
    """
    monkeypatch.delenv('CLIENT_ID', raising=False)
    monkeypatch.delenv('CLIENT_SECRET', raising=False)

    with caplog.at_level(logging.WARNING, logger='mkdocs.plugins'):
        hooks.on_pre_build(config=_config({}))

    assert caplog.records == []


def test_on_pre_build_never_warns_when_auth_is_off(caplog):
    """Turning auth off is a deliberate config choice, not a build fault."""
    with caplog.at_level(logging.WARNING, logger='mkdocs.plugins'):
        hooks.on_pre_build(config=_config({'auth': {'enabled': False}}))

    assert caplog.records == []


def test_on_template_context_exposes_auth_settings():
    """Template context gains the auth flag and the resolved policy."""
    config = _config(
        {
            'auth': {
                'enabled': True,
                'allowed_domains': ['example.com'],
                'allowed_emails': [],
            }
        }
    )
    hooks.on_pre_build(config=config)
    context = {'page': 'home'}

    returned = hooks.on_template_context(
        context, template_name='main.html', config=config
    )

    assert returned is context
    assert context['auth_enabled'] is True
    assert context['auth_config']['allowed_domains'] == ['example.com']


def test_on_page_markdown_returns_markdown_unchanged():
    """The page markdown hook is a pass-through in this project."""
    config = _config({})

    returned = hooks.on_page_markdown(
        '# Title', page=None, config=config, files=None
    )

    assert returned == '# Title'
