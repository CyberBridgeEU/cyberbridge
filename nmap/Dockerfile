# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and nmap
# We need to update apt first and install the required packages
RUN apt-get update && apt-get install -y \
    nmap \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for requirements installation
WORKDIR /

# Copy requirements from project root
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set back to app directory
WORKDIR /app

# Copy application code
COPY app/ .

# Expose port for FastAPI
EXPOSE 8000

# Command to run the application -> old docker image port was 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]