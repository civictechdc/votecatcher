-- Comprehensive cleanup script for VoteCatcher
-- This script will delete all storage objects, tables, functions, types, and extensions

-- First, delete all storage objects from both buckets
DELETE FROM storage.objects WHERE bucket_id = 'voter-files';
DELETE FROM storage.objects WHERE bucket_id = 'petitions';

-- Note: We cannot drop storage.buckets as it's managed by Supabase
-- The buckets will remain but will be empty after deleting all objects

-- Drop all tables and functions
DROP TABLE IF EXISTS registration_matches CASCADE;
DROP TABLE IF EXISTS registration_data CASCADE;
DROP TABLE IF EXISTS file_processing_status CASCADE;
DROP TABLE IF EXISTS voter_records CASCADE;
DROP TABLE IF EXISTS api_key_usage CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS campaign CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS insert_top_matches(UUID);
DROP FUNCTION IF EXISTS ensure_single_active_campaign();
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop types
DROP TYPE IF EXISTS campaign_status;
DROP TYPE IF EXISTS provider_enum;

-- Note: This script will completely clean up the database schema and storage
-- Run this only when you want to start fresh with a clean slate 