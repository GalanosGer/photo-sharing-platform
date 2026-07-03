#!/bin/bash

set -e

# ---- Παραμετροποίηση ----
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-k29photo}"
DB_PASS="${DB_PASS:-}"
APP_FILE="${APP_FILE:-app.py}"
VENV_DIR="${VENV_DIR:-venv}"

export PGPASSWORD="$DB_PASS"

# ---- 1) Python venv ----
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating Python virtual environment in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

echo ">>> Activating virtual environment ..."

source "$VENV_DIR/bin/activate"


echo ">>> Installing Python libraries from requirements.txt ..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet


echo ">>> Preparing PostgreSQL database '$DB_NAME' on $DB_HOST:$DB_PORT ..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    echo ">>> Database '$DB_NAME' created."
else
    echo ">>> Database '$DB_NAME' already exists."
fi


echo ">>> Truncating all tables in database '$DB_NAME' ..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -c "
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE;';
    END LOOP;
END \$\$;"

echo ">>> Applying schema (schema.sql) ..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f schema.sql

echo ">>> Loading sample data (data.sql) ..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f data.sql

echo ">>> Database setup completed."

# Start Flask
echo ">>> Starting Flask application"
python3 "$APP_FILE"