# Docker Setup with External PostgreSQL

This guide explains how to run the CyberBridge REST API with an external PostgreSQL container.

## Environment Variables

The following environment variables can be configured:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `postgres` | PostgreSQL container name or IP address |
| `DB_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `postgres` | Database username |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `postgres` | Database name |

## Running with Docker Run

```bash
# Build the image
docker build -t cyberbridge-api .

# Run with your PostgreSQL container
docker run -d \
  --name cyberbridge-api \
  -p 8000:8000 \
  -e DB_HOST=your_postgres_container \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=your_database \
  --network your_network \
  cyberbridge-api
```

## Running with Docker Compose

1. Copy the example compose file:
```bash
cp docker-compose.example.yml docker-compose.yml
```

2. Edit `docker-compose.yml` to match your PostgreSQL setup:
   - Update `DB_HOST` to your PostgreSQL container name
   - Set the correct database credentials
   - Configure the network settings

3. Run the services:
```bash
docker-compose up -d
```

## Network Configuration

Make sure both containers are on the same Docker network:

```bash
# Create a network (if not exists)
docker network create mynetwork

# Run PostgreSQL container on the network
docker run -d \
  --name postgres-db \
  --network mynetwork \
  -e POSTGRES_PASSWORD=mypassword \
  postgres:15

# Run CyberBridge API on the same network
docker run -d \
  --name cyberbridge-api \
  --network mynetwork \
  -p 8000:8000 \
  -e DB_HOST=postgres-db \
  -e POSTGRES_PASSWORD=mypassword \
  cyberbridge-api
```

## Migration Handling

The container automatically:
1. Waits for the database to be ready
2. Runs Alembic migrations (`alembic upgrade head`)
3. Starts the FastAPI application

If migrations fail, the container will exit with an error code.

## Logs

To view logs and migration status:
```bash
docker logs cyberbridge-api
```

## Development vs Production

- **Development**: Override environment variables as needed
- **Production**: Use Docker secrets or secure environment variable management

## Production Deployment with Custom Domains

For production deployment with custom domains (e.g., `https://access.cyberbridge.eu` for frontend and `https://api.cyberbridge.eu` for backend):

### Frontend Setup

1. Build the frontend Docker image with the production API URL:
```bash
cd cyberbridge_frontend
docker build \
  --build-arg VITE_PRODUCTION_IP=https://api.cyberbridge.eu \
  -t cyberbridge-frontend:latest .
```

2. Run the frontend container:
```bash
docker run -d \
  --name cyberbridge-frontend \
  -p 5173:5173 \
  cyberbridge-frontend:latest
```

### Backend Setup

1. Build the backend Docker image:
```bash
cd cyberbridge_backend
docker build -t cyberbridge-backend:latest .
```

2. Run the backend container:
```bash
docker run -d \
  --name cyberbridge-backend \
  --network mynetwork \
  -p 8000:8000 \
  -e DB_HOST=postgres-db \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=cyberbridge_db \
  cyberbridge-backend:latest
```

### Reverse Proxy Configuration

Configure your reverse proxy (Nginx/Apache) to:

1. **Frontend**: Route `https://access.cyberbridge.eu` → `localhost:5173`
2. **Backend**: Route `https://api.cyberbridge.eu` → `localhost:5174`

**Example Nginx configuration:**

```nginx
# Frontend
server {
    listen 443 ssl;
    server_name access.cyberbridge.eu;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 443 ssl;
    server_name api.cyberbridge.eu;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location / {
        proxy_pass http://localhost:5174;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### CORS Configuration

Ensure the backend allows requests from your frontend domain. Update `app/main.py`:

```python
origins = [
    "https://access.cyberbridge.eu",
    "http://localhost:5173",  # For local development
]
```

### SSL/TLS Certificates

Use Let's Encrypt for free SSL certificates:

```bash
sudo certbot --nginx -d access.cyberbridge.eu -d api.cyberbridge.eu
```