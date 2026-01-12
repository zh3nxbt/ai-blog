-- Migration: Create blog_content_drafts table
-- Task: db-002
-- Description: Table to store draft iterations with quality scores and critique

CREATE TABLE IF NOT EXISTS blog_content_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blog_post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    content TEXT,
    title TEXT,
    quality_score NUMERIC(3,2),
    critique JSONB,
    api_cost_cents INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint on blog_post_id and iteration_number
    CONSTRAINT unique_blog_post_iteration UNIQUE (blog_post_id, iteration_number)
);

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_blog_content_drafts_blog_post_id
    ON blog_content_drafts(blog_post_id);

-- Add comment for documentation
COMMENT ON TABLE blog_content_drafts IS 'Stores draft iterations for blog posts with quality scores and critique from the Ralph loop';
COMMENT ON COLUMN blog_content_drafts.iteration_number IS 'Sequential iteration number for this blog post (1, 2, 3, ...)';
COMMENT ON COLUMN blog_content_drafts.quality_score IS 'Quality score from 0.00 to 1.00 (stored as numeric(3,2))';
COMMENT ON COLUMN blog_content_drafts.critique IS 'JSON critique from quality validator with improvements suggested';
COMMENT ON COLUMN blog_content_drafts.api_cost_cents IS 'API cost in cents for generating this iteration';
