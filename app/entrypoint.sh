#!/bin/sh

# Set env vars if needed (can be overridden by Docker/Compose)
export FLASK_APP=app:create_app
export FLASK_ENV=production

# Initialize DB (ignore errors if already initialized)
flask db init || true
flask db migrate -m "Auto migration" || true
flask db upgrade

# Start Gunicorn
exec gunicorn -b 0.0.0.0:5000 "app:create_app()"
