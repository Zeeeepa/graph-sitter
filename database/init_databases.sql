-- =============================================================================
-- DATABASE INITIALIZATION SCRIPT
-- =============================================================================
-- This script creates 7 specialized databases with dedicated users and passwords
-- for the graph-sitter system. Each database handles a specific domain.
-- =============================================================================

-- Create databases
CREATE DATABASE task_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE projects_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE prompts_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE codebase_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE analytics_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE events_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE learning_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';

-- Create dedicated users with strong passwords
CREATE USER task_user WITH PASSWORD 'task_secure_2024!';
CREATE USER projects_user WITH PASSWORD 'projects_secure_2024!';
CREATE USER prompts_user WITH PASSWORD 'prompts_secure_2024!';
CREATE USER codebase_user WITH PASSWORD 'codebase_secure_2024!';
CREATE USER analytics_user WITH PASSWORD 'analytics_secure_2024!';
CREATE USER events_user WITH PASSWORD 'events_secure_2024!';
CREATE USER learning_user WITH PASSWORD 'learning_secure_2024!';

-- Grant database ownership to respective users
ALTER DATABASE task_db OWNER TO task_user;
ALTER DATABASE projects_db OWNER TO projects_user;
ALTER DATABASE prompts_db OWNER TO prompts_user;
ALTER DATABASE codebase_db OWNER TO codebase_user;
ALTER DATABASE analytics_db OWNER TO analytics_user;
ALTER DATABASE events_db OWNER TO events_user;
ALTER DATABASE learning_db OWNER TO learning_user;

-- Grant connection privileges
GRANT CONNECT ON DATABASE task_db TO task_user;
GRANT CONNECT ON DATABASE projects_db TO projects_user;
GRANT CONNECT ON DATABASE prompts_db TO prompts_user;
GRANT CONNECT ON DATABASE codebase_db TO codebase_user;
GRANT CONNECT ON DATABASE analytics_db TO analytics_user;
GRANT CONNECT ON DATABASE events_db TO events_user;
GRANT CONNECT ON DATABASE learning_db TO learning_user;

-- Create a read-only user for cross-database analytics
CREATE USER analytics_readonly WITH PASSWORD 'analytics_readonly_2024!';
GRANT CONNECT ON DATABASE task_db TO analytics_readonly;
GRANT CONNECT ON DATABASE projects_db TO analytics_readonly;
GRANT CONNECT ON DATABASE prompts_db TO analytics_readonly;
GRANT CONNECT ON DATABASE codebase_db TO analytics_readonly;
GRANT CONNECT ON DATABASE analytics_db TO analytics_readonly;
GRANT CONNECT ON DATABASE events_db TO analytics_readonly;
GRANT CONNECT ON DATABASE learning_db TO analytics_readonly;

-- Create a superuser for administration
CREATE USER graph_sitter_admin WITH PASSWORD 'admin_secure_2024!' SUPERUSER;

