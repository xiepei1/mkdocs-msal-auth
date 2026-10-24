"""Tests for environment parsing and mkdocs.yml auth configuration."""

import pytest


@pytest.mark.parametrize(
    ('value', 'default', 'expected'),
    [
        ('1', False, True),
        ('true', False, True),
        ('TRUE', False, True),
        ('yes', False, True),
        ('on', False, True),
        ('0', True, False),
        ('false', True, False),
        ('no', True, False),
        ('off', True, False),
        # Unknown and empty strings must not be treated as truthy.
        ('', True, False),
        ('garbage', True, False),
    ],
)
def test_env_bool_parses_flag_strings(server, monkeypatch, value, default, expected):
    """Env flags parse per word, not by Python truthiness of the raw string."""
    monkeypatch.setenv('MKDOCS_TEST_FLAG', value)

    assert server._env_bool('MKDOCS_TEST_FLAG', default=default) is expected


def test_env_bool_uses_default_when_unset(server, monkeypatch):
    """A missing variable falls back to the caller's default."""
    monkeypatch.delenv('MKDOCS_TEST_FLAG', raising=False)

    assert server._env_bool('MKDOCS_TEST_FLAG', default=True) is True
    assert server._env_bool('MKDOCS_TEST_FLAG', default=False) is False


def test_env_bool_ignores_surrounding_whitespace(server, monkeypatch):
    """Whitespace around a flag value does not change its meaning."""
    monkeypatch.setenv('MKDOCS_TEST_FLAG', '  TRUE  ')

    assert server._env_bool('MKDOCS_TEST_FLAG', default=False) is True


def _write_mkdocs(tmp_path, body):
    config_path = tmp_path / 'mkdocs.yml'
    config_path.write_text(body, encoding='utf-8')
    return config_path


def test_loads_allow_lists_from_mkdocs(server, monkeypatch, tmp_path):
    """extra.auth allow-lists land in the module globals the gate reads."""
    config_path = _write_mkdocs(
        tmp_path,
        'extra:\n'
        '  auth:\n'
        '    enabled: true\n'
        '    allowed_domains:\n'
        '      - example.com\n'
        '    allowed_emails:\n'
        '      - boss@other.com\n',
    )
    monkeypatch.setattr(server, 'MKDOCS_CONFIG_PATH', config_path)

    server._load_auth_config_from_mkdocs()

    assert server.AUTH_ENABLED is True
    assert server.ALLOWED_DOMAINS == ['example.com']
    assert server.ALLOWED_EMAILS == ['boss@other.com']


def test_missing_extra_auth_keeps_open_defaults(server, monkeypatch, tmp_path):
    """An absent extra.auth means auth on with no allow-list restrictions."""
    config_path = _write_mkdocs(tmp_path, 'site_name: docs\n')
    monkeypatch.setattr(server, 'MKDOCS_CONFIG_PATH', config_path)

    server._load_auth_config_from_mkdocs()

    assert server.AUTH_ENABLED is True
    assert server.ALLOWED_DOMAINS == []
    assert server.ALLOWED_EMAILS == []


def test_null_extra_auth_keeps_open_defaults(server, monkeypatch, tmp_path):
    """An explicit empty auth mapping must not disable authentication."""
    config_path = _write_mkdocs(tmp_path, 'extra:\n  auth:\n')
    monkeypatch.setattr(server, 'MKDOCS_CONFIG_PATH', config_path)

    server._load_auth_config_from_mkdocs()

    assert server.AUTH_ENABLED is True
    assert server.ALLOWED_DOMAINS == []
    assert server.ALLOWED_EMAILS == []


def test_enabled_false_disables_auth(server, monkeypatch, tmp_path):
    """extra.auth.enabled: false turns the auth gate off."""
    config_path = _write_mkdocs(
        tmp_path, 'extra:\n  auth:\n    enabled: false\n'
    )
    monkeypatch.setattr(server, 'MKDOCS_CONFIG_PATH', config_path)

    server._load_auth_config_from_mkdocs()

    assert server.AUTH_ENABLED is False


def test_bare_extra_key_keeps_open_defaults(server, monkeypatch, tmp_path):
    """A bare ``extra:`` with no children must not stop the process booting.

    ``yaml.safe_load`` reads that shape as ``{'extra': None}``. The loader
    promises to keep defaults when a section is unavailable, so this must
    not raise.
    """
    config_path = _write_mkdocs(tmp_path, 'site_name: docs\nextra:\n')
    monkeypatch.setattr(server, 'MKDOCS_CONFIG_PATH', config_path)

    server._load_auth_config_from_mkdocs()

    assert server.AUTH_ENABLED is True
    assert server.ALLOWED_DOMAINS == []
    assert server.ALLOWED_EMAILS == []


def test_non_mapping_auth_keeps_open_defaults(server, monkeypatch, tmp_path):
    """An ``extra.auth`` that is not a mapping is ignored, not raised.

    ``auth: yes`` parses to the boolean ``True``. Feeding that to
    ``dict.update`` raises, which would take the whole server down at
    import time.
    """
    config_path = _write_mkdocs(tmp_path, 'extra:\n  auth: yes\n')
    monkeypatch.setattr(server, 'MKDOCS_CONFIG_PATH', config_path)

    server._load_auth_config_from_mkdocs()

    assert server.AUTH_ENABLED is True
    assert server.ALLOWED_DOMAINS == []
    assert server.ALLOWED_EMAILS == []


def test_missing_config_file_keeps_existing_values(server, monkeypatch, tmp_path):
    """A missing mkdocs.yml must not crash or clobber loaded settings."""
    monkeypatch.setattr(server, 'MKDOCS_CONFIG_PATH', tmp_path / 'absent.yml')
    monkeypatch.setattr(server, 'AUTH_ENABLED', True)
    monkeypatch.setattr(server, 'ALLOWED_DOMAINS', ['keep.example.com'])
    monkeypatch.setattr(server, 'ALLOWED_EMAILS', ['keep@example.com'])

    server._load_auth_config_from_mkdocs()

    assert server.ALLOWED_DOMAINS == ['keep.example.com']
    assert server.ALLOWED_EMAILS == ['keep@example.com']
