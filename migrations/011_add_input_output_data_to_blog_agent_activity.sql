-- Migration: Add input_data and output_data columns to blog_agent_activity
-- Description: Add JSONB columns to store detailed input/output data for agent activities
--              This provides full transparency into agent decision-making, especially for
--              juice evaluation where we want to see all RSS sources and LLM reasoning.

ALTER TABLE blog_agent_activity
ADD COLUMN IF NOT EXISTS input_data JSONB,
ADD COLUMN IF NOT EXISTS output_data JSONB;

-- Add comments
COMMENT ON COLUMN blog_agent_activity.input_data IS 'Input data provided to the agent (e.g., source items for juice evaluation)';
COMMENT ON COLUMN blog_agent_activity.output_data IS 'Output data produced by the agent (e.g., LLM response)';
