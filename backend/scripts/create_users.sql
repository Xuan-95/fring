-- User creation script
-- Instructions:
-- 1. Run: python scripts/hash_password.py
-- 2. Copy generated hashes and replace <hash-here> below
-- 3. Run: psql $DATABASE_URL -f scripts/create_users.sql

INSERT INTO users (username, email, password_hash, is_active) VALUES
('user1', 'user1@fring.local', '<hash-here>', true),
('user2', 'user2@fring.local', '<hash-here>', true);
