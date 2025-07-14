-- PostgreSQL initialization script for MCP PKI database
-- This script creates the necessary database structure

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_user') THEN
        CREATE USER mcp_user WITH PASSWORD 'mcp_password';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mcp_pki TO mcp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS pki;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions on schemas
GRANT ALL PRIVILEGES ON SCHEMA pki TO mcp_user;
GRANT ALL PRIVILEGES ON SCHEMA audit TO mcp_user;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mcp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mcp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA pki GRANT ALL ON TABLES TO mcp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA pki GRANT ALL ON SEQUENCES TO mcp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO mcp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON SEQUENCES TO mcp_user;
