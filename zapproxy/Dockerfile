# Start from Python 3.12
FROM python:3.12-slim

# Install Java (for ZAP) and other basics
RUN apt-get update && apt-get install -y openjdk-21-jre-headless wget

# Set up a working directory for FastAPI
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and extract ZAP to /zap
WORKDIR /zap
RUN wget https://github.com/zaproxy/zaproxy/releases/download/v2.16.1/ZAP_2.16.1_Linux.tar.gz \
    && tar -xvzf ZAP_2.16.1_Linux.tar.gz \
    && rm ZAP_2.16.1_Linux.tar.gz

# Copy your FastAPI code from host "app/" to container "/app"
WORKDIR /app
COPY . /app

# Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app

# Expose FastAPI (8000) and ZAP (8080)
EXPOSE 8000 8080

# Copy and use entrypoint script (cleans stale ZAP data on startup + periodic purge)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]