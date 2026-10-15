#!/bin/bash
set -e

echo "Current migration version:"
alembic current -v || echo "No migrations applied yet"

echo "Applying migrations..."
alembic upgrade head

echo "New migration version:"
alembic current
exec "$@"
