# AGENTS

This repository builds docs with MkDocs and the Material theme, and serves
them via Flask with Microsoft Entra ID (MSAL) authentication.

## Start Here

- Read project overview and setup: [README.md](README.md), [docs/setup.md](docs/setup.md)
- Auth and serving entrypoint: [app/webapp/server.py](app/webapp/server.py)
- MkDocs build hooks: [app/mkdocs_msal_auth/hooks.py](app/mkdocs_msal_auth/hooks.py)
- Auth policy tests, which document the security contract: [tests/](tests/)

## Common Commands

Dependencies are managed with [uv](https://docs.astral.sh/uv/).
`pyproject.toml` is the source of truth and `uv.lock` pins exact versions.

```bash
uv sync                 # install runtime and dev dependencies
uv run pytest           # run the test suite
uv run ruff check .     # lint
uv run mkdocs build     # build docs into site/
uv run mkdocs serve     # preview docs
uv run python -m app.webapp.server
```

Tests need no Entra ID credentials and make no network calls. MSAL and
Microsoft Graph are replaced with fakes at their network boundary.

## Runtime Configuration

Authentication config is runtime-driven from environment variables. Do not
hardcode secrets.

- Required: `CLIENT_ID`, `CLIENT_SECRET`, and (`TENANT_ID` or `AUTHORITY`)
- Required for Flask session security: `SECRET_KEY`

`mkdocs.yml` also controls auth behavior under `extra.auth`:

- `enabled`
- `allowed_domains`
- `allowed_emails`

## Working Conventions

- Keep code Python 3 compatible and simple. Avoid heavy dependencies.
- Preserve the current auth flow shape:
  - `/auth/login` starts authorization
  - `/auth/authorized` handles callback and session creation
  - `/auth/verify` reports current auth status
  - `/auth/logout` clears session
- Prefer small, targeted edits over broad refactors.
- When you change auth behavior, add or change a test first. Then update
  docs and keep `README.md` consistent.

## Before You Finish

Run all of these after any auth or config change.

1. `uv run pytest` proves the auth behavior still holds.
2. `uv run ruff check .` lints the tree.
3. `uv run mkdocs build --strict` proves docs compile.
4. `uv run python -m app.webapp.server` to see the login redirect and the
   callback behavior for yourself.

## Known Pitfalls

- Missing env vars leave MSAL partially configured. `/auth/login` then
  returns 500 instead of redirecting.
- `AUTHORITY` defaults to `https://login.microsoftonline.com/<TENANT_ID>`
  when you do not set it.
- `SECRET_KEY` is mandatory. The server raises at import without it,
  because that key signs the session cookie that grants access to the
  docs. A fixed fallback is a public signing key, so anyone can forge
  `session['user']`. The test suite sets a throwaway value in
  `tests/conftest.py`.
- MSAL reserves `openid`, `profile` and `offline_access` and adds them
  to every request. When the caller passes any of them, MSAL raises
  `ValueError`. Keep `SCOPES` in `app/webapp/server.py` free of those
  three. `tests/conftest.py` enforces the same rule in the fake, so a
  regression fails the suite instead of passing it.
- The auth exemptions in `app/webapp/server.py` (`AUTH_PATHS_EXEMPT`) are
  security-sensitive. Review changes to them with care. `_is_exempt_path`
  normalizes the request path and matches each entry on a path-segment
  boundary. Keep both properties. If you drop the normalization, a
  request for `/assets/../setup/` reclaims the `/assets/` exemption and
  serves protected pages to anonymous callers. If you match by raw
  prefix, `/auth` also exempts `/authorize`.
- The Dockerfile runs `COPY . .`. `.dockerignore` is what keeps `.env`,
  which holds `CLIENT_SECRET`, out of the image. Keep it in step with
  any new local secret file.
- MkDocs calls build hooks with `config`, `template_name`, `page` and
  `files` as keyword arguments. A hook that takes them positionally
  raises `TypeError` during `mkdocs build`. When you edit them, match
  the signatures in `app/mkdocs_msal_auth/hooks.py`.
- `mkdocs build --strict` turns log warnings into build errors. Keep
  hook logging at info level so a build without Entra credentials still
  succeeds. The docs build does not use those credentials.
- `mkdocs-simple-hooks` is what runs `app/mkdocs_msal_auth/hooks.py`. If
  you remove that plugin, the hooks stop running and nothing in the
  build reports it.
