"""MkDocs hooks for exposing auth settings to generated templates.

Hook signatures match the MkDocs 1.6.1 plugin API. MkDocs passes
``config``, ``template_name``, ``page`` and ``files`` as keyword
arguments, so accepting them positionally raises ``TypeError`` at build
time.
"""

import logging
import os
from typing import Any

logger = logging.getLogger('mkdocs.plugins')

AUTH_ENABLED = True


def _default_auth_config() -> dict[str, Any]:
    """Return default auth behavior when ``extra.auth`` is omitted.

    Returns:
        Default auth settings consumed by hooks and templates.
    """
    return {
        'enabled': True,
        'allowed_domains': [],
        'allowed_emails': [],
    }


def _resolve_auth_config(config: Any) -> dict[str, Any]:
    """Return the auth settings for a MkDocs config mapping.

    A bare ``extra:`` parses to None, and an ``auth:`` holding a scalar
    parses to a non-mapping. Either means "no override", so the defaults
    are kept instead of raising.

    Args:
        config: MkDocs configuration mapping.

    Returns:
        Auth settings with defaults filled in for absent keys.
    """
    auth_config = _default_auth_config()
    extra = config.get('extra') if isinstance(config, dict) else None
    auth_section = extra.get('auth') if isinstance(extra, dict) else None
    if isinstance(auth_section, dict):
        auth_config.update(auth_section)
    return auth_config


def on_pre_build(*, config: Any) -> None:
    """Initialize authentication context before MkDocs starts building.

    Args:
        config: MkDocs configuration mapping.
    """
    global AUTH_ENABLED

    auth_config = _resolve_auth_config(config)
    AUTH_ENABLED = bool(auth_config['enabled'])

    # These are notices, not build faults. MkDocs --strict turns log
    # warnings into build errors, and building the docs needs no Entra
    # credentials at all. Keep them informational so a secretless build
    # still succeeds.
    if not AUTH_ENABLED:
        logger.info('Authentication is disabled in configuration')

    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')

    if AUTH_ENABLED and (not client_id or not client_secret):
        logger.info(
            'MSAL/Azure AD credentials not found in environment variables.'
        )
        logger.info(
            'Set CLIENT_ID and CLIENT_SECRET '
            '(and TENANT_ID or AUTHORITY) environment variables.'
        )


def on_page_markdown(markdown: str, /, **kwargs: Any) -> str:
    """Return page markdown unchanged.

    Args:
        markdown: Markdown content for the current page.
        **kwargs: Remaining hook arguments from MkDocs.

    Returns:
        Original markdown content.
    """
    return markdown


def on_template_context(
    context: dict[str, Any], /, *, template_name: str, config: Any
) -> dict[str, Any]:
    """Expose auth configuration in the template rendering context.

    Args:
        context: Template context mapping for the current template.
        template_name: Name of the template being rendered.
        config: MkDocs configuration mapping.

    Returns:
        The same context mapping with auth settings added.
    """
    auth_config = _resolve_auth_config(config)

    context['auth_enabled'] = AUTH_ENABLED
    context['auth_config'] = auth_config

    return context
