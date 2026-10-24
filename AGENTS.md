# AGENTS

This repository builds docs with MkDocs and the Material theme, and serves
them via Flask with Microsoft Entra ID (MSAL) authentication.

## Start Here

- Read project overview and setup: [README.md](README.md), [docs/setup.md](docs/setup.md)
- Auth and serving entrypoint: [src/webapp/server.py](src/webapp/server.py)
- MkDocs build hooks: [src/mkdocs_msal_auth/hooks.py](src/mkdocs_msal_auth/hooks.py)
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
uv run python -m src.webapp.server
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
4. `python3 scripts/smoke_token.py` checks env wiring. It needs real
   credentials and is the only step that cannot run without them.
5. `uv run python -m src.webapp.server` to see the login redirect and the
   callback behavior for yourself.

## Known Pitfalls

- Missing env vars leave MSAL partially configured. `/auth/login` then
  returns 500 instead of redirecting.
- `AUTHORITY` defaults to `https://login.microsoftonline.com/<TENANT_ID>`
  when you do not set it.
- The auth exemptions in `src/webapp/server.py` (`AUTH_PATHS_EXEMPT`) are
  security-sensitive. Review changes to them with care.
- `AUTH_PATHS_EXEMPT` matches by prefix, so it is looser than it looks.
  `/auth` exempts every path that starts with those five characters and
  `/login` exempts everything under `/login/`. Anything a future page
  places at those prefixes is served with no authentication. The tests
  cover the intended contract, where auth routes and assets are exempt and
  docs pages are not. They do not pin this looseness on purpose, so that
  fixing it does not break the suite.
- MkDocs calls build hooks with `config`, `template_name`, `page` and
  `files` as keyword arguments. A hook that takes them positionally
  raises `TypeError` during `mkdocs build`. When you edit them, match
  the signatures in `src/mkdocs_msal_auth/hooks.py`.
- `mkdocs build --strict` turns log warnings into build errors. Keep
  hook logging at info level so a build without Entra credentials still
  succeeds. The docs build does not use those credentials.
- `mkdocs-simple-hooks` is what runs `src/mkdocs_msal_auth/hooks.py`. If
  you remove that plugin, the hooks stop running and nothing in the
  build reports it.
