"""Expose the Flask application for production WSGI servers."""

from src.webapp.server import app

__all__ = ["app"]
