-- Migration: Create blog_agent_activity table
-- Task: db-003
-- Description: Table to log all agent activity with timing and success metrics

CREATE TABLE IF NOT EXISTS blog_agent_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    context_id UUID,
    duration_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_blog_agent_activity_agent_name
    ON blog_agent_activity(agent_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_blog_agent_activity_activity_type
    ON blog_agent_activity(activity_type, created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE blog_agent_activity IS 'Logs all agent activity for monitoring and debugging the Ralph loop';
COMMENT ON COLUMN blog_agent_activity.agent_name IS 'Name of the agent (e.g., ProductMarketingAgent, CritiqueAgent)';
COMMENT ON COLUMN blog_agent_activity.activity_type IS 'Type of activity (e.g., content_draft, critique, publish)';
COMMENT ON COLUMN blog_agent_activity.context_id IS 'Optional UUID linking to related entity (e.g., blog_post_id)';
COMMENT ON COLUMN blog_agent_activity.duration_ms IS 'Duration of the activity in milliseconds';
COMMENT ON COLUMN blog_agent_activity.success IS 'Whether the activity completed successfully';
COMMENT ON COLUMN blog_agent_activity.error_message IS 'Error message if success=false';
COMMENT ON COLUMN blog_agent_activity.metadata IS 'Additional JSON metadata about the activity';
