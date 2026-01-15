-- Migration: Create blog_topic_sources and blog_topic_items tables
-- Task: mix-001
-- Description: Unified topic source tables for mixed sourcing

CREATE TABLE IF NOT EXISTS blog_topic_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL CHECK (source_type IN ('rss', 'evergreen', 'standards', 'vendor', 'internal')),
    name TEXT NOT NULL,
    category TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER CHECK (priority >= 1 AND priority <= 10),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blog_topic_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES blog_topic_sources(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT,
    url TEXT,
    content TEXT,
    published_at TIMESTAMPTZ,
    used_in_blog UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blog_topic_items_source_id
    ON blog_topic_items(source_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_blog_topic_items_unique_url
    ON blog_topic_items(url)
    WHERE url IS NOT NULL;

COMMENT ON TABLE blog_topic_sources IS 'Unified source registry for RSS, evergreen, standards, vendor, and internal sources';
COMMENT ON COLUMN blog_topic_sources.source_type IS 'Source type: rss, evergreen, standards, vendor, internal';
COMMENT ON COLUMN blog_topic_sources.name IS 'Human-readable source name';
COMMENT ON COLUMN blog_topic_sources.category IS 'Optional category or grouping label';
COMMENT ON COLUMN blog_topic_sources.active IS 'Whether this source is active for ingestion';
COMMENT ON COLUMN blog_topic_sources.priority IS 'Priority ranking 1-10 (10=highest priority)';
COMMENT ON COLUMN blog_topic_sources.notes IS 'Optional notes about the source';

COMMENT ON TABLE blog_topic_items IS 'Unified topic items across all source types';
COMMENT ON COLUMN blog_topic_items.source_id IS 'Foreign key to blog_topic_sources';
COMMENT ON COLUMN blog_topic_items.title IS 'Topic or article title';
COMMENT ON COLUMN blog_topic_items.summary IS 'Short summary or outline';
COMMENT ON COLUMN blog_topic_items.url IS 'Optional source URL (nullable)';
COMMENT ON COLUMN blog_topic_items.content IS 'Optional full text or notes';
COMMENT ON COLUMN blog_topic_items.published_at IS 'Original publication timestamp if available';
COMMENT ON COLUMN blog_topic_items.used_in_blog IS 'Foreign key to blog_posts if used in a blog post';
COMMENT ON COLUMN blog_topic_items.metadata IS 'Source-specific metadata as JSON';
