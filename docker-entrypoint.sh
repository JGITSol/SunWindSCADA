#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Apply database migrations
echo "Applying database migrations..."
python django_backend/manage.py migrate

# Populate the database with initial data
echo "Populating database with wind turbine data..."
python django_backend/manage.py populate_turbines

# Start the server
echo "Starting server..."
exec uvicorn django_backend.config.asgi:application --host 0.0.0.0 --port 8000 --reload
