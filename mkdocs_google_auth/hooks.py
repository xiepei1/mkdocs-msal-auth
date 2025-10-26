# MkDocs Google Authentication Hooks
import os
import re
import json
import logging
from pathlib import Path
from functools import wraps

logger = logging.getLogger('mkdocs.plugins')

# Configuration
AUTH_ENABLED = True  # Set to False to disable authentication during development
AUTH_PATHS_EXEMPT = ['/login/', '/auth/', '/assets/', '/javascripts/', '/stylesheets/']

def on_pre_build(config, **kwargs):
    """Hook that runs before the build starts."""
    logger.info("Initializing Google Authentication for MkDocs")

    # Get auth configuration from mkdocs.yml
    extra_config = config.get('extra', {})
    auth_config = extra_config.get('auth', {})

    # Check if auth is enabled in config
    global AUTH_ENABLED
    AUTH_ENABLED = auth_config.get('enabled', True)

    if not AUTH_ENABLED:
        logger.warning("Authentication is disabled in configuration")

    # Check for environment variables
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

    if AUTH_ENABLED and (not client_id or not client_secret):
        logger.warning("Google OAuth credentials not found in environment variables.")
        logger.warning("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")

    return config

def on_page_markdown(markdown, page, config, files, **kwargs):
    """Hook for processing markdown, useful for adding auth-related markers."""
    # Special handling for login page
    if page.file.src_uri == 'login.md':
        return markdown

    # Nothing to modify for other pages
    return markdown

def on_pre_template(template_name, template_context, config, **kwargs):
    """Hook that runs before rendering a template."""
    # Add auth info to template context
    extra_config = config.get('extra', {})
    auth_config = extra_config.get('auth', {})

    template_context['auth_enabled'] = AUTH_ENABLED
    template_context['auth_config'] = auth_config

    return template_context

# Helper function for server implementation
def check_auth(func):
    """Decorator to check if a user is authenticated."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Import here to avoid circular imports
        from flask import request, redirect

        # Check if authentication is enabled
        if not AUTH_ENABLED:
            return func(*args, **kwargs)

        # Check if path is exempt from auth
        request_path = request.path
        for exempt_path in AUTH_PATHS_EXEMPT:
            if request_path.startswith(exempt_path):
                return func(*args, **kwargs)

        # Check for auth token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return redirect('/login/')

        token = auth_header.split(' ')[1]
        # Verify token (implementation depends on how you store and validate tokens)

        return func(*args, **kwargs)

    return decorated_function