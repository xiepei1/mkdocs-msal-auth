# AGENTS

This repository builds MkDocs static docs and serves them via Flask with Microsoft Entra ID (MSAL) authentication.

## Start Here

- Read project overview and setup: [README.md](README.md)
- Read docs content and auth pages: [docs/index.md](docs/index.md), [docs/login.md](docs/login.md), [docs/setup.md](docs/setup.md)
- Auth + serving entrypoint: [src/webapp/server.py](src/webapp/server.py)
- MkDocs auth-related hooks: [src/mkdocs_msal_auth/hooks.py](src/mkdocs_msal_auth/hooks.py)

## Common Commands

```bash
pip install -r requirements.txt
cp .env.example .env
mkdocs build
python -m src.webapp.server
python3 scripts/smoke_token.py
```

## Runtime Configuration

Authentication config is runtime-driven from environment variables. Do not hardcode secrets.

- Required: `CLIENT_ID`, `CLIENT_SECRET`, and (`TENANT_ID` or `AUTHORITY`)
- Required for Flask session security: `SECRET_KEY`

`mkdocs.yml` also controls auth behavior under `extra.auth`:

- `enabled`
- `allowed_domains`
- `allowed_emails`

## Working Conventions

- Keep code Python 3 compatible and simple; avoid adding heavy dependencies unless necessary.
- Preserve the current auth flow shape:
  - `/auth/login` starts authorization
  - `/auth/authorized` handles callback and session creation
  - `/auth/verify` reports current auth status
  - `/auth/logout` clears session
- Prefer small, targeted edits over broad refactors.
- When changing auth behavior, update docs and keep `README.md` consistent.

## Validation Checklist

After auth or config changes:

1. Run `python3 scripts/smoke_token.py` to validate env wiring.
2. Run `mkdocs build` to ensure docs compile.
3. Run `python -m src.webapp.server` and verify login redirect/callback behavior.

## Known Pitfalls

- Missing env vars cause partially configured MSAL app.
- `AUTHORITY` defaults to `https://login.microsoftonline.com/<TENANT_ID>` when not explicitly set.
- Auth exemptions in `src/webapp/server.py` (`AUTH_PATHS_EXEMPT`) are security-sensitive; review changes carefully.
