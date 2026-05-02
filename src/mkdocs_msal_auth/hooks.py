"""MkDocs hooks for exposing auth settings to generated templates."""

import os
import logging
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


def on_pre_build(config, **kwargs):
    """Initialize authentication context before MkDocs starts building.

    Args:
        config: MkDocs configuration dictionary.
        **kwargs: Additional hook arguments from MkDocs.

    Returns:
        The unmodified MkDocs configuration dictionary.
    """
    logger.info('Initializing Microsoft Entra ID authentication settings for MkDocs')

    auth_config = _default_auth_config()
    auth_config.update(config.get('extra', {}).get('auth', {}) or {})

    # Check if auth is enabled in config
    global AUTH_ENABLED
    AUTH_ENABLED = bool(auth_config['enabled'])

    if not AUTH_ENABLED:
        logger.warning('Authentication is disabled in configuration')

    # Check for environment variables (MSAL/Azure AD)
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')

    if AUTH_ENABLED and (not client_id or not client_secret):
        logger.warning(
            'MSAL/Azure AD credentials not found in environment variables.'
        )
        logger.warning(
            'Set CLIENT_ID and CLIENT_SECRET '
            '(and TENANT_ID or AUTHORITY) environment variables.'
        )

    return config


def on_page_markdown(markdown, page, config, files, **kwargs):
    """Return page markdown unchanged.

    Args:
        markdown: Markdown content for the current page.
        page: MkDocs page object.
        config: MkDocs configuration dictionary.
        files: MkDocs files collection.
        **kwargs: Additional hook arguments from MkDocs.

    Returns:
        Original markdown content.
    """
    return markdown


def on_pre_template(template_name, template_context, config, **kwargs):
    """Expose auth configuration in the template rendering context.

    Args:
        template_name: Template file being rendered.
        template_context: Template context dictionary.
        config: MkDocs configuration dictionary.
        **kwargs: Additional hook arguments from MkDocs.

    Returns:
        Updated template context containing auth settings.
    """
    auth_config = _default_auth_config()
    auth_config.update(config.get('extra', {}).get('auth', {}) or {})

    template_context['auth_enabled'] = AUTH_ENABLED
    template_context['auth_config'] = auth_config

    return template_context