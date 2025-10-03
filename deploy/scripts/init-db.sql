-- Initialize database with common extensions and default app role
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- Create application role if not exists
DO $$
BEGIN
   IF NOT EXISTS (
       SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user'
   ) THEN
       CREATE ROLE app_user LOGIN PASSWORD 'changeme' NOSUPERUSER NOCREATEDB NOCREATEROLE;
   END IF;
END
$$;

-- Grant privileges on database
-- Replace with actual database name or manage grants via migrations
-- GRANT ALL PRIVILEGES ON DATABASE rail_django_graphql TO app_user;