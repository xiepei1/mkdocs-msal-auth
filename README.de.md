# Docs + Flask + Microsoft-Entra-ID-Authentifizierung

[English](README.md) | [简体中文](README.zh-CN.md) | Deutsch

[![CI](https://github.com/xiepei1/mkdocs-msal-auth/actions/workflows/ci.yml/badge.svg)](https://github.com/xiepei1/mkdocs-msal-auth/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MkDocs](https://img.shields.io/badge/MkDocs-1.6.1-000000)](https://www.mkdocs.org/)
[![uv](https://img.shields.io/badge/deps-uv-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)](#lizenz)

Dieses Projekt baut Dokumentation mit [MkDocs](https://www.mkdocs.org/) und dem [Material](https://squidfunk.github.io/mkdocs-material/)-Theme. Flask stellt die erzeugte statische Website bereit. Der Zugriff ist mit Microsoft Entra ID (Azure AD) geschützt. Auf der Python-Seite verwendet das Projekt MSAL.

## Architektur

1. MkDocs baut statisches HTML in den Ordner `site/`.
2. Flask stellt Dateien aus `site/` bereit.
3. Nicht angemeldete Nutzer werden zur Microsoft-Entra-ID-Anmeldung umgeleitet.
4. Nach der Anmeldung speichert Flask die Benutzeridentität in einer sicheren Sitzung.
5. Optional schränken Sie den Zugriff nach E-Mail-Domain und nach bestimmten E-Mail-Adressen ein.

## Funktionen

- Doku mit MkDocs und dem Material-Theme
- Flask-Server für die bereitgestellte HTML-Ausgabe
- Microsoft-Entra-ID-OAuth2-Autorisierungscode-Flow über MSAL
- Zugriffskontrolle mit `allowed_domains` und `allowed_emails`
- Laufzeitkonfiguration aus Umgebungsvariablen. Für die lokale Entwicklung gibt es `.env`.

## Schnellstart

Abhängigkeiten verwaltet [uv](https://docs.astral.sh/uv/).

1. Abhängigkeiten installieren:

```bash
uv sync
```

2. Umgebungsvariablenvorlage kopieren und Werte eintragen:

```bash
cp .env.example .env
```

3. Doku bauen:

```bash
uv run mkdocs build
```

4. Lokalen Server starten:

```bash
uv run python -m app.webapp.server
```

5. `http://localhost:5000` öffnen.

## Dokumentation schreiben

Sie schreiben den Inhalt als Markdown-Dateien in `docs/`. MkDocs baut diese Dateien zu statischem HTML in `site/`. Der Flask-Server stellt dieses HTML bereit, nachdem er den Anmeldestatus bestätigt hat. Jede Seite unter `docs/` gehört zur geschützten Website.

### Seite hinzufügen

1. Erstellen Sie eine Markdown-Datei unter `docs/`. Die Datei `docs/guides/api.md` wird zur URL `/guides/api/`.
2. Setzen Sie eine Überschrift der Ebene 1 an den Dateianfang. Das Theme zeigt diese Überschrift als Seitentitel.
3. Verlinken Sie andere Seiten mit Pfaden relativ zur aktuellen Datei. Der Link `[Setup](setup.md)` funktioniert aus `docs/index.md`.
4. Führen Sie `uv run mkdocs build` aus und lesen Sie die Ausgabe. Stellen Sie sicher, dass der Build keine Fehler meldet.

### Menüreihenfolge festlegen

`mkdocs.yml` hat keinen `nav`-Schlüssel. Daher baut das Material-Theme das Menü aus der Ordnerstruktur und den Dateinamen. Wenn Sie eine feste Reihenfolge und eigene Titel wollen, fügen Sie `mkdocs.yml` einen `nav`-Schlüssel hinzu:

```yaml
nav:
  - Home: index.md
  - Setup: setup.md
  - Writing: writing.md
```

Pfade in `nav` sind relativ zu `docs/`. MkDocs baut Seiten, die in `nav` fehlen, und listet sie im Build-Log. Diese Seiten bleiben über die URL erreichbar.

### Seiten in Ordnern organisieren

Ein Unterordner unter `docs/` wird ein URL-Pfadsegment. Eine Seite in `docs/guides/` erhält eine URL, die mit `/guides/` beginnt. Ordnernamen werden zu URL-Namen. Verwenden Sie kurze Namen mit Bindestrichen. Vermeiden Sie Leerzeichen und Großbuchstaben.

### Bilder und statische Dateien hinzufügen

Legen Sie Bilder und andere statische Dateien unter `docs/assets/` ab. Verlinken Sie sie mit Pfaden relativ zur Seitendatei. Die Datei `docs/assets/diagram.png` braucht aus `docs/index.md` den Link `assets/diagram.png`. Aus `docs/guides/api.md` braucht sie den Link `../assets/diagram.png`.

Platzieren Sie keinen privaten Inhalt unter `/auth/`, `/login/`, `/assets/`, `/images/`, `/javascripts/` oder `/stylesheets/`. Der Server stellt diese Pfadpräfixe ohne Anmeldeschritt bereit. Daher kann jeder diesen Inhalt lesen.

### Werte mit Makros wiederverwenden

Das macros-Plugin ist aktiviert. Es ersetzt Jinja-Ausdrücke in Ihrem Markdown zur Build-Zeit durch Werte. Definieren Sie einen Wert unter `extra` in `mkdocs.yml`:

```yaml
extra:
  owner: Platform Team
```

Danach verwenden Sie ihn auf jeder Seite:

```markdown
This site is maintained by {{ owner }}.
```

Das Plugin gibt Ihrem Markdown auch `config`, `page`, `files` und `navigation`. Eine Seite kann eigene Werte in einem YAML-Front-Matter-Block am Dateianfang definieren. Wenn die Seite ein literales `{{` oder `}}` zeigen muss, umschließen Sie diesen Text mit `{% raw %}` und `{% endraw %}`.

### Vorschau und erneuter Build

1. Führen Sie `uv run mkdocs serve` für eine Live-Vorschau aus. Sie lädt bei jedem Speichern neu. Diese Vorschau hat keinen Anmeldeschritt.
2. Führen Sie `uv run mkdocs build` nach jeder Bearbeitungsrunde aus. Der Flask-Server liest `site/`. Er baut die Doku nicht neu.

Der Build führt die Hooks in `app/mkdocs_msal_auth/hooks.py` über `mkdocs-simple-hooks` aus. Die Hooks lesen `extra.auth` und geben dessen Werte an die Theme-Templates weiter. Sie ändern Ihr Seiten-Markdown nicht.

## Entwicklung

```bash
uv run pytest            # run the test suite
uv run ruff check .      # lint
uv run mkdocs serve      # live docs preview
```

Der Testlauf braucht keine Entra-ID-Zugangsdaten. Er macht keine Netzwerkaufrufe. Er deckt die Zugriffs-Allowlist, die Ausnahmepfad-Regeln, das Laden der Konfiguration und jeden Zweig des Anmelde- und Callback-Ablaufs ab.

`pyproject.toml` ist die Quelle der Wahrheit für Abhängigkeiten. `uv.lock` pinnt exakte Versionen. Führen Sie `uv sync` nach dem Ziehen von Änderungen aus. Fügen Sie eine Abhängigkeit mit `uv add <package>` und ein Entwicklungstool mit `uv add --dev <package>` hinzu.

## Produktivbetrieb (WSGI)

Verwenden Sie Gunicorn mit dem WSGI-Einstiegspunkt:

```bash
.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 app.webapp.wsgi:app
```

Optionale Absicherung:

- Wenn Sie über HTTPS bereitstellen, setzen Sie `SESSION_COOKIE_SECURE=true`.
- Setzen Sie immer einen starken `SECRET_KEY`.

## Erforderliche Umgebungsvariablen

- `CLIENT_ID`: Entra-Anwendungs-ID (Client-ID)
- `CLIENT_SECRET`: Entra-Client-Secret
- `TENANT_ID`: Entra-Mandanten-ID
- `AUTHORITY` (optional): überschreibt den Standard `https://login.microsoftonline.com/<TENANT_ID>`
- `SECRET_KEY`: Signaturschlüssel für die Flask-Sitzung

## Entra-App-Registrierung

Im Microsoft Entra Admin Center:

1. Registrieren Sie eine Anwendung.
2. Fügen Sie eine Web-Umleitungs-URI hinzu: `http://localhost:5000/auth/authorized`. Alternativ tragen Sie Ihre Produktiv-URL ein.
3. Erstellen Sie ein Client-Secret.
4. Gewähren Sie die delegierte Berechtigung `User.Read` (Microsoft Graph).

## Auth-Richtlinien-Konfiguration

`extra.auth` in `mkdocs.yml` ist optional. Wenn es ganz fehlt, arbeitet die Anwendung weiterhin mit diesen Standardwerten:

- Authentifizierung aktiviert
- keine Domain-Allowlist
- keine E-Mail-Allowlist

Fügen Sie diesen Abschnitt hinzu, um die Standardwerte zu überschreiben:

```yaml
extra:
  auth:
    enabled: true
    allowed_domains: []
    allowed_emails: []
```

Verhalten:

- Wenn `extra.auth` fehlt, gilt die MSAL-Authentifizierung weiterhin mit dem Standardverhalten.
- Wenn beide Listen leer sind, ist jeder erfolgreich authentifizierte Entra-Nutzer zugelassen.
- Wenn eine der Listen Einträge hat, muss der Nutzer zu einer der erlaubten Domains oder E-Mail-Adressen passen.

## Docker

```bash
docker build -t mkdocs-msal-auth .
docker run -p 5000:5000 \
  -e CLIENT_ID="your-client-id" \
  -e CLIENT_SECRET="your-client-secret" \
  -e TENANT_ID="your-tenant-id" \
  -e SECRET_KEY="your-secret-key" \
  -e SESSION_COOKIE_SECURE=true \
  mkdocs-msal-auth
```

Das Image installiert Abhängigkeiten aus `uv.lock`. Es baut die Doku-Website zur Image-Build-Zeit.

## Smoke-Check

Der schnellste Weg, den Auth-Ablauf zu sehen, ist der Serverstart und das Öffnen der Website. Eine nicht authentifizierte Anfrage für `/` muss zu `/auth/login` umleiten.

## Quellstruktur

```
.
├── .claude/settings.json       Allowliste für Agent-Befehle
├── .github/
│   ├── instructions/           Verweis auf AGENTS.md
│   └── workflows/ci.yml        Lint, Test und Build bei jedem Push
├── app/                        gesamter Python-Code
│   ├── mkdocs_msal_auth/
│   │   └── hooks.py            MkDocs-Build-Hooks für Auth-Einstellungen
│   └── webapp/
│       ├── server.py           Flask-Anwendung und Entra-Auth-Ablauf
│       └── wsgi.py             produktiver WSGI-Einstiegspunkt
├── docs/                       Markdown, das MkDocs baut
│   ├── assets/                 Stile der Anmeldeseite und Fehlerskript
│   ├── index.md
│   ├── login.md
│   └── setup.md
├── tests/                      pytest-Suite, ohne Netzwerk und Zugangsdaten
│   ├── conftest.py             Fixtures und Fakes an der MSAL- und Graph-Grenze
│   ├── test_auth_policy.py     Allowlist- und Ausnahmepfad-Regeln
│   ├── test_config.py          Laden von Env und mkdocs.yml
│   ├── test_hooks.py           Verträge der MkDocs-Build-Hooks
│   └── test_routes.py          Anmeldung, Callback, Abmeldung und statische Auslieferung
├── AGENTS.md                   Agent-Leitfaden, die einzige Quelle der Wahrheit
├── CLAUDE.md                   Verweis auf AGENTS.md
├── Dockerfile                  baut site/ und stellt es mit Gunicorn bereit
├── LICENSE                     MIT-Lizenz
├── mkdocs.yml                  MkDocs-Konfiguration und die extra.auth-Richtlinie
├── pyproject.toml              Abhängigkeiten und Tool-Konfiguration
└── .python-version             gefixte Python-Version
```

Die Flask-Anwendung liegt unter `app/webapp/`. Die MkDocs-Build-Hooks liegen unter `app/mkdocs_msal_auth/`. Doku-Inhalte liegen unter `docs/`. Tests liegen unter `tests/` und berühren nie das Netzwerk. Dateien unter `.cache/`, `.pytest_cache/`, `.ruff_cache/`, `site/` und `.venv/` sind erzeugt. Git trackt sie nicht.

## Lizenz

MIT. Den vollständigen Text finden Sie unter [LICENSE](LICENSE).
