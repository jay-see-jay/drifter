ALTER TABLE users
DROP
COLUMN access_token,
DROP
COLUMN refresh_token,
DROP
COLUMN token_expires_at,
ADD COLUMN clerk_user_id VARCHAR(255) NOT NULL UNIQUE;