#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "$POSTGRES_HOST" -p "$PGPORT" -U "$POSTGRES_USER" > /dev/null 2>&1; do
  sleep 1
done

echo "Checking database..."
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$PGPORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then
  echo "Creating database $POSTGRES_DB..."
  PGPASSWORD="$POSTGRES_PASSWORD" createdb -h "$POSTGRES_HOST" -p "$PGPORT" -U "$POSTGRES_USER" "$POSTGRES_DB"
else
  echo "Database $POSTGRES_DB already exists"
fi

echo "Running migrations..."
cd /backend && alembic upgrade head

exec "$@"