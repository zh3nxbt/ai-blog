-- Migration: Create database indexes for query performance
-- Task: db-006
-- Description: Add performance indexes for frequently queried tables

-- Index for blog_content_drafts ordered by iteration_number descending
-- Used when retrieving the latest draft for a blog post
CREATE INDEX IF NOT EXISTS idx_blog_content_drafts_post_iteration
    ON blog_content_drafts(blog_post_id, iteration_number DESC);

-- NOTE: Indexes for blog_agent_activity already created in migration 003:
--   - idx_blog_agent_activity_agent_name on (agent_name, created_at DESC)
--   - idx_blog_agent_activity_activity_type on (activity_type, created_at DESC)

-- Partial index for blog_rss_items where used_in_blog IS NULL
-- Used for finding unused RSS items available for new blog posts
CREATE INDEX IF NOT EXISTS idx_blog_rss_items_unused
    ON blog_rss_items(created_at DESC)
    WHERE used_in_blog IS NULL;

-- Add comments for documentation
COMMENT ON INDEX idx_blog_content_drafts_post_iteration IS 'Optimizes queries for latest draft iterations per blog post';
COMMENT ON INDEX idx_blog_rss_items_unused IS 'Optimizes queries for unused RSS items available for content generation';
