-- Database initialization script for SWHA Backend
-- This script runs when PostgreSQL container is first created

-- Create database if not exists (handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS swha_db;

-- Create user if not exists (handled by POSTGRES_USER env var)
-- CREATE USER IF NOT EXISTS swha_user WITH PASSWORD 'swha_password';

-- Grant privileges to user
GRANT ALL PRIVILEGES ON DATABASE swha_db TO swha_user;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas if needed
-- (FastAPI SQLAlchemy will create tables automatically)

-- Create indexes for better performance
-- These will be applied after tables are created by SQLAlchemy

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'SWHA Database initialized successfully at %', NOW();
END $$; 