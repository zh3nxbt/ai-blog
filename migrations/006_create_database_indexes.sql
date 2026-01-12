-- Migration: Create database indexes for query performance
-- Task: db-006
-- Description: Add performance indexes for frequently queried tables

-- Index for blog_content_drafts ordered by iteration_number descending
-- Used when retrieving the latest draft for a blog post
CREATE INDEX IF NOT EXISTS idx_blog_content_drafts_post_iteration
    ON blog_content_drafts(blog_post_id, iteration_number DESC);

-- Index for blog_agent_activity by agent_name and created_at
-- Used for activity reports and logging queries
CREATE INDEX IF NOT EXISTS idx_blog_agent_activity_agent_time
    ON blog_agent_activity(agent_name, created_at DESC);

-- Index for blog_agent_activity by activity_type and created_at
-- Used for filtering by activity type (e.g., all 'content_draft' activities)
CREATE INDEX IF NOT EXISTS idx_blog_agent_activity_type_time
    ON blog_agent_activity(activity_type, created_at DESC);

-- Partial index for blog_rss_items where used_in_blog IS NULL
-- Used for finding unused RSS items available for new blog posts
CREATE INDEX IF NOT EXISTS idx_blog_rss_items_unused
    ON blog_rss_items(created_at DESC)
    WHERE used_in_blog IS NULL;

-- Add comments for documentation
COMMENT ON INDEX idx_blog_content_drafts_post_iteration IS 'Optimizes queries for latest draft iterations per blog post';
COMMENT ON INDEX idx_blog_agent_activity_agent_time IS 'Optimizes activity reports by agent name';
COMMENT ON INDEX idx_blog_agent_activity_type_time IS 'Optimizes activity reports by activity type';
COMMENT ON INDEX idx_blog_rss_items_unused IS 'Optimizes queries for unused RSS items available for content generation';
