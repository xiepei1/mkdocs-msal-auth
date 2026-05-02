# Welcome

This site demonstrates a documentation platform built with three components:

1. MkDocs generates static documentation pages.
2. Flask hosts the generated HTML under the `site/` directory.
3. Microsoft Entra ID (via MSAL) authenticates users before access is granted.

## What You Get

- Familiar MkDocs authoring workflow
- Simple Flask hosting model for static output
- Enterprise sign-in with Microsoft identity platform
- Optional allow-lists for domains and individual email accounts

## Request Flow

1. User requests a docs page.
2. Flask checks whether the user already has a valid session.
3. If not authenticated, user is redirected to `/auth/login`.
4. Entra ID completes login and redirects to `/auth/authorized`.
5. Flask validates identity and stores user email in session.
6. Flask serves the requested static page from `site/`.

## Configuration Summary

Authentication behavior can be customized via `mkdocs.yml`, but the `extra.auth` section is optional. When omitted, the app still authenticates through Microsoft Entra ID with default settings.

Optional override example:

```yaml
extra:
  auth:
    enabled: true
    allowed_domains: []
    allowed_emails: []
```

See [Setup](setup.md) for complete installation and Microsoft Entra registration details.