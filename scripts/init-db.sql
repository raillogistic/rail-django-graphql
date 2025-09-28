-- Script d'initialisation de la base de données PostgreSQL
-- pour Django GraphQL Auto System

-- Créer la base de données principale si elle n'existe pas
SELECT 'CREATE DATABASE django_graphql_auto'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'django_graphql_auto')\gexec

-- Créer la base de données de test si elle n'existe pas
SELECT 'CREATE DATABASE django_graphql_auto_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'django_graphql_auto_test')\gexec

-- Créer la base de données de développement si elle n'existe pas
SELECT 'CREATE DATABASE django_graphql_auto_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'django_graphql_auto_dev')\gexec

-- Créer un utilisateur pour l'application si il n'existe pas
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'django_user') THEN

      CREATE ROLE django_user LOGIN PASSWORD 'django_password';
   END IF;
END
$do$;

-- Accorder les privilèges nécessaires
GRANT ALL PRIVILEGES ON DATABASE django_graphql_auto TO django_user;
GRANT ALL PRIVILEGES ON DATABASE django_graphql_auto_test TO django_user;
GRANT ALL PRIVILEGES ON DATABASE django_graphql_auto_dev TO django_user;

-- Se connecter à la base de données principale
\c django_graphql_auto;

-- Créer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Créer un schéma pour les fonctions personnalisées
CREATE SCHEMA IF NOT EXISTS django_graphql_auto;

-- Fonction pour générer des slugs
CREATE OR REPLACE FUNCTION django_graphql_auto.generate_slug(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            regexp_replace(
                unaccent(input_text),
                '[^a-zA-Z0-9\s-]', '', 'g'
            ),
            '\s+', '-', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Fonction pour la recherche full-text
CREATE OR REPLACE FUNCTION django_graphql_auto.search_text(
    search_query TEXT,
    search_fields TEXT[]
)
RETURNS TEXT AS $$
BEGIN
    RETURN array_to_string(search_fields, ' ') ILIKE '%' || search_query || '%';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Index pour améliorer les performances de recherche
-- (sera créé automatiquement par Django lors des migrations)

-- Configuration des paramètres de performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Recharger la configuration
SELECT pg_reload_conf();

-- Créer une table pour le suivi des versions de schéma
CREATE TABLE IF NOT EXISTS django_graphql_auto.schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(100) DEFAULT current_user,
    migration_files TEXT[],
    rollback_sql TEXT
);

-- Insérer la version initiale
INSERT INTO django_graphql_auto.schema_versions (version, description, migration_files)
VALUES ('1.0.0', 'Version initiale du schéma Django GraphQL Auto', ARRAY['0001_initial'])
ON CONFLICT (version) DO NOTHING;

-- Créer une fonction pour enregistrer les versions de schéma
CREATE OR REPLACE FUNCTION django_graphql_auto.register_schema_version(
    p_version VARCHAR(50),
    p_description TEXT DEFAULT NULL,
    p_migration_files TEXT[] DEFAULT NULL,
    p_rollback_sql TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO django_graphql_auto.schema_versions (
        version, description, migration_files, rollback_sql
    )
    VALUES (p_version, p_description, p_migration_files, p_rollback_sql)
    ON CONFLICT (version) DO UPDATE SET
        description = EXCLUDED.description,
        migration_files = EXCLUDED.migration_files,
        rollback_sql = EXCLUDED.rollback_sql,
        applied_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Créer une vue pour les statistiques de performance
CREATE OR REPLACE VIEW django_graphql_auto.performance_stats AS
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY schemaname, tablename, attname;

-- Créer une fonction pour nettoyer les anciennes données de log
CREATE OR REPLACE FUNCTION django_graphql_auto.cleanup_old_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Cette fonction sera utilisée pour nettoyer les logs anciens
    -- L'implémentation dépendra des tables de log créées par Django
    
    -- Exemple pour une table de logs hypothétique
    -- DELETE FROM django_admin_log 
    -- WHERE action_time < NOW() - INTERVAL '%s days', days_to_keep;
    
    -- GET DIAGNOSTICS deleted_count = ROW_COUNT;
    deleted_count := 0; -- Placeholder
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Créer un utilisateur en lecture seule pour les rapports
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'django_readonly') THEN

      CREATE ROLE django_readonly LOGIN PASSWORD 'readonly_password';
   END IF;
END
$do$;

-- Accorder les privilèges de lecture seule
GRANT CONNECT ON DATABASE django_graphql_auto TO django_readonly;
GRANT USAGE ON SCHEMA public TO django_readonly;
GRANT USAGE ON SCHEMA django_graphql_auto TO django_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO django_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA django_graphql_auto TO django_readonly;

-- Accorder automatiquement les privilèges sur les nouvelles tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO django_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA django_graphql_auto GRANT SELECT ON TABLES TO django_readonly;

-- Message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Base de données Django GraphQL Auto initialisée avec succès!';
    RAISE NOTICE 'Utilisateurs créés: django_user (lecture/écriture), django_readonly (lecture seule)';
    RAISE NOTICE 'Extensions installées: uuid-ossp, pg_trgm, unaccent';
    RAISE NOTICE 'Schéma personnalisé: django_graphql_auto';
END $$;