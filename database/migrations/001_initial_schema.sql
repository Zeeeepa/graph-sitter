-- Migration 001: Initial Schema Creation
-- This migration creates the complete database schema for the graph-sitter project

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Migration metadata
INSERT INTO schema_migrations (version, description, applied_at) 
VALUES ('001', 'Initial schema creation', NOW())
ON CONFLICT (version) DO NOTHING;

-- Execute the main schema
\i database/schema/models.sql

-- Verify migration
DO $$
BEGIN
    -- Check that all main tables exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
        RAISE EXCEPTION 'Migration failed: organizations table not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'codebases') THEN
        RAISE EXCEPTION 'Migration failed: codebases table not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
        RAISE EXCEPTION 'Migration failed: tasks table not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'prompts') THEN
        RAISE EXCEPTION 'Migration failed: prompts table not created';
    END IF;
    
    RAISE NOTICE 'Migration 001 completed successfully';
END $$;

