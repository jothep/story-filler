#!/bin/bash
set -e

echo "Waiting for database..."
python << END
import sys
import time
import psycopg2

for i in range(30):
    try:
        conn = psycopg2.connect(
            dbname="maori_story_dev",
            user="devuser",
            password="REMOVED_CREDENTIAL",
            host="db",
            port="5432"
        )
        conn.close()
        print("Database is ready!")
        sys.exit(0)
    except psycopg2.OperationalError:
        if i == 29:
            print("Database connection failed after 30 attempts")
            sys.exit(1)
        time.sleep(1)
END

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Creating logs directory..."
mkdir -p logs

echo "Starting development server..."
python manage.py runserver 0.0.0.0:8000
