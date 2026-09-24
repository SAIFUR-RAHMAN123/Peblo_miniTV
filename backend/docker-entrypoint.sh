#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import time
import sqlalchemy
from app.core.config import get_settings

settings = get_settings()
for attempt in range(30):
    try:
        engine = sqlalchemy.create_engine(settings.database_url)
        conn = engine.connect()
        conn.close()
        print('Database is ready.')
        break
    except Exception as e:
        print(f'Attempt {attempt + 1}/30: database not ready ({e}); retrying in 1s...')
        time.sleep(1)
else:
    raise SystemExit('Database never became ready.')
"

echo "Running migrations..."
alembic upgrade head

echo "Seeding database (no-op if already seeded)..."
python -m app.seed

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000