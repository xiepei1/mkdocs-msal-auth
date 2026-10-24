FROM python:3.12-slim

WORKDIR /app

# Install uv from the official image so dependency versions come from uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /bin/

# Install locked dependencies first to keep the layer cache warm across
# source changes. Runtime deps only; docs are built in the next step.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

# Copy project files
COPY . .

# Build the MkDocs site
RUN .venv/bin/mkdocs build

# The project is not installed as a package (see [tool.uv] package = false),
# so the app is imported from the working directory.
ENV PYTHONPATH=/app

# Expose port for the WSGI app
EXPOSE 5000

# Run the server using a production-grade WSGI server
CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "src.webapp.wsgi:app"]
