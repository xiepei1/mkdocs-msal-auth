"""Expose the Flask application for production WSGI servers."""

from app.webapp.server import app

__all__ = ["app"]
