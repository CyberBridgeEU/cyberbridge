#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done

>&2 echo "Database is up - executing migrations"

# Check if this is a fresh database (no alembic_version table)
if ! PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM alembic_version LIMIT 1" 2>/dev/null; then
    # Fresh database - create tables from models and stamp
    echo "Fresh database detected - creating tables from models..."
    python3 -c "from app.database.database import engine, Base; from app.models.models import *; Base.metadata.create_all(bind=engine)"

    if [ $? -eq 0 ]; then
        echo "Tables created successfully"
    else
        echo "Table creation failed"
        exit 1
    fi

    # Mark all migrations as applied
    echo "Marking migrations as applied..."
    alembic stamp head

    if [ $? -eq 0 ]; then
        echo "Migrations marked successfully"
    else
        echo "Migration marking failed"
        exit 1
    fi
else
    # Existing database - run migrations normally
    echo "Existing database detected - running migrations..."
    alembic upgrade head

    if [ $? -eq 0 ]; then
        echo "Migrations completed successfully"
    else
        echo "Migration failed"
        exit 1
    fi
fi

# Start the application
echo "Starting the application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'