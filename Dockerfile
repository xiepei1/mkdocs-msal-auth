FROM python:3.12-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Build the MkDocs site
RUN mkdocs build

# Expose port for the WSGI app
EXPOSE 5000

# Run the server using a production-grade WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "wsgi:app"]