-- Migration: Add authentication fields to users table
-- Run with: psql $DATABASE_URL -f migrations/001_add_auth_fields.sql

ALTER TABLE users
ADD COLUMN password_hash VARCHAR(255),
ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
