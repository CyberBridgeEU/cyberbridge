FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including Tor
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    tor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run Tor, migrations, and start server
CMD ["sh", "-c", "tor --RunAsDaemon 1 --SocksPort 9050 && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"]
