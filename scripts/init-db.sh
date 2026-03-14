#!/bin/bash
set -e

echo "=== Init DB: Creating biosec schema ==="
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE SCHEMA IF NOT EXISTS biosec;
    COMMENT ON SCHEMA biosec IS 'Schema nghiệp vụ chính cho BIOSECURITY OS 2026';
EOSQL
echo "=== Init DB: Done ==="
