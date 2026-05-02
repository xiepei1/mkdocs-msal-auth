---
applyTo: '**/**.py'
---
This project uses MSAL for Python to authenticate access to a MkDocs-generated site served by Flask.

For Python changes in this repo:

- Do not hardcode credentials or tenant values.
- Load runtime auth config from environment variables (`CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`, optional `AUTHORITY`) via `python-dotenv`.
- Preserve current Flask auth route behavior in `src/webapp/server.py` (`/auth/login`, `/auth/authorized`, `/auth/verify`, `/auth/logout`).
- Keep `mkdocs.yml` `extra.auth` compatibility (`enabled`, `allowed_domains`, `allowed_emails`).
- Prefer focused edits and maintain backward-compatible behavior unless a breaking change is explicitly requested.