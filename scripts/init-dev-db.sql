-- VoteCatcher Development Database Initialization Script
-- This script is run automatically when the PostgreSQL container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create a schema for development data if needed
-- CREATE SCHEMA IF NOT EXISTS dev_data;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE votecatcher TO votecatcher;
GRANT ALL ON SCHEMA public TO votecatcher;

-- Add comments for documentation
COMMENT ON DATABASE votecatcher IS 'VoteCatcher Development Database';
COMMENT ON EXTENSION "uuid-ossp" IS 'Provides UUID generation functions';
COMMENT ON EXTENSION "pg_trgm" IS 'Provides text similarity functions for fuzzy matching';
