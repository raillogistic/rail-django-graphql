-- Initial PostgreSQL setup for the application
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Example app role; change in real deployments
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user'
    ) THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'changeme';
    END IF;
END
$$;