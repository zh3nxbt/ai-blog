-- Migration: Create blog_rss_items table
-- Task: db-005
-- Description: Table to store individual RSS feed items with foreign key relationships

CREATE TABLE IF NOT EXISTS blog_rss_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES blog_rss_sources(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    summary TEXT,
    published_at TIMESTAMPTZ,
    used_in_blog UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_blog_rss_items_source_id
    ON blog_rss_items(source_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_blog_rss_items_published_at
    ON blog_rss_items(published_at DESC);

-- Add comments for documentation
COMMENT ON TABLE blog_rss_items IS 'Individual RSS feed items fetched from sources';
COMMENT ON COLUMN blog_rss_items.source_id IS 'Foreign key to blog_rss_sources table';
COMMENT ON COLUMN blog_rss_items.title IS 'Title of the RSS item';
COMMENT ON COLUMN blog_rss_items.url IS 'URL of the RSS item (must be unique)';
COMMENT ON COLUMN blog_rss_items.summary IS 'Summary or excerpt from the RSS item';
COMMENT ON COLUMN blog_rss_items.published_at IS 'Publication timestamp from RSS feed';
COMMENT ON COLUMN blog_rss_items.used_in_blog IS 'Foreign key to blog_posts if used in a blog post';
