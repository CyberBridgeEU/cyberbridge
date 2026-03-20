# Use Python 3.12 slim as the base image
FROM python:3.12-slim

# Install PostgreSQL client for database health checks and git for GitHub repo cloning
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Copy startup script and make it executable
COPY start.sh .
RUN chmod +x start.sh

# Accept build argument for production backend URL (for email verification and password reset links)
ARG API_BASE_URL_PROD=https://api.cyberbridge.eu
ENV API_BASE_URL_PROD=$API_BASE_URL_PROD

# Set default environment variables for database connection
# These can be overridden at runtime via docker run -e or docker-compose
ENV CONTAINER_ENV=docker
ENV DB_HOST=cyberbridge_db
ENV DB_PORT=5432
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=postgres

# Set scanner service URLs for Docker network
# Use container names as hostnames, with port 8000 (internal container port)
ENV NMAP_SERVICE_URL=http://nmap:8000
ENV SEMGREP_SERVICE_URL=http://semgrep:8000
ENV OSV_SERVICE_URL=http://osv:8000
ENV ZAP_SERVICE_URL=http://zap:8000

# Expose port 8000
EXPOSE 8000

# Use the startup script as the entry point
CMD ["./start.sh"]