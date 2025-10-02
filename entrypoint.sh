#!/bin/sh
# This script runs the database setup before starting the web server.

echo "Running database setup..."
python /app/BE/Database.py

echo "Starting Gunicorn server..."

exec "$@"