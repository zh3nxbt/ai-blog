-- Migration: Create blog_rss_sources table
-- Task: db-004
-- Description: Table to manage RSS feed sources for content aggregation

CREATE TABLE IF NOT EXISTS blog_rss_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER CHECK (priority >= 1 AND priority <= 10),
    last_fetched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_blog_rss_sources_active_priority
    ON blog_rss_sources(active, priority DESC);

-- Add comments for documentation
COMMENT ON TABLE blog_rss_sources IS 'RSS feed sources for aggregating manufacturing industry news';
COMMENT ON COLUMN blog_rss_sources.name IS 'Human-readable name of the RSS source';
COMMENT ON COLUMN blog_rss_sources.url IS 'URL of the RSS/Atom feed';
COMMENT ON COLUMN blog_rss_sources.category IS 'Category or topic of the feed (e.g., manufacturing, CNC, automation)';
COMMENT ON COLUMN blog_rss_sources.active IS 'Whether this source should be fetched';
COMMENT ON COLUMN blog_rss_sources.priority IS 'Priority ranking 1-10 (10=highest priority)';
COMMENT ON COLUMN blog_rss_sources.last_fetched_at IS 'Timestamp of last successful fetch';
