---
applyTo: '**/**.py'
---
This is a project that uses Microsoft Authentication Library (MSAL) for Python to implement SSO authentication for mkdocs-generated documentation sites. The project includes hooks for integrating MSAL authentication into the mkdocs build process.
The current code is built on google auth version, and is actually broken due to outdated Python version and library versions, as well as some code issues.
The task is to update the code to use MSAL for Python instead of Google Auth, ensuring compatibility with the latest versions of Python and mkdocs. The updated code should include proper authentication flows, token management, and integration with mkdocs hooks.
The `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`, and `AUTHORITY` variables are passed into Python flask run during runtime, and should not be hardcoded in the code. They are provided as environment variables in `.env` file and loaded using `python-dotenv`.