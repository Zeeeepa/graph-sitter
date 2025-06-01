-- Schema migrations tracking table
-- This table keeps track of which migrations have been applied

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    checksum VARCHAR(64),
    execution_time INTERVAL,
    applied_by VARCHAR(255) DEFAULT CURRENT_USER
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at);

-- Function to check if a migration has been applied
CREATE OR REPLACE FUNCTION migration_applied(migration_version VARCHAR(50))
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(SELECT 1 FROM schema_migrations WHERE version = migration_version);
END;
$$ LANGUAGE plpgsql;

-- Function to record a migration
CREATE OR REPLACE FUNCTION record_migration(
    migration_version VARCHAR(50),
    migration_description TEXT,
    migration_checksum VARCHAR(64) DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO schema_migrations (version, description, checksum, applied_at)
    VALUES (migration_version, migration_description, migration_checksum, NOW())
    ON CONFLICT (version) DO UPDATE SET
        applied_at = NOW(),
        checksum = EXCLUDED.checksum;
END;
$$ LANGUAGE plpgsql;

