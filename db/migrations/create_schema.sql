-- create_schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS repos (
    repo_id TEXT PRIMARY KEY,            -- GitHub GraphQL node id (stable)
    full_name TEXT NOT NULL UNIQUE,      -- owner/name
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT,
    stars INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    repo_updated_at TIMESTAMP WITH TIME ZONE,
    last_crawled_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);
-- Index on stars
-- Purpose: We often query repos by star count (top repos, star ranges, etc.)
-- Benefit: Makes ORDER BY stars and WHERE stars > X queries extremely fast
-- Reason: Stars change over time and analytics commonly use this field
CREATE INDEX IF NOT EXISTS idx_repos_stars ON repos(stars);

-- Index on owner
-- Purpose: Fast lookup of repos belonging to a specific GitHub user/org
-- Benefit: SELECT * FROM repos WHERE owner = 'google' becomes instant
-- Reason: Future phases may crawl or analyze repos by owner frequently
CREATE INDEX IF NOT EXISTS idx_repos_owner ON repos(owner);
