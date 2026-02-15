-- Migration 015: Add RSS source health tracking columns
-- Task: reliability
-- Description:
--   Track source fetch failures and auto-disable chronic offenders.

ALTER TABLE blog_rss_sources
ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER NOT NULL DEFAULT 0;

ALTER TABLE blog_rss_sources
ADD COLUMN IF NOT EXISTS last_failed_at TIMESTAMPTZ;

ALTER TABLE blog_rss_sources
ADD COLUMN IF NOT EXISTS last_error TEXT;

-- Backfill nulls for existing rows.
UPDATE blog_rss_sources
SET consecutive_failures = 0
WHERE consecutive_failures IS NULL;

COMMENT ON COLUMN blog_rss_sources.consecutive_failures IS
    'Number of consecutive fetch failures for this source';

COMMENT ON COLUMN blog_rss_sources.last_failed_at IS
    'Timestamp of the most recent fetch failure';

COMMENT ON COLUMN blog_rss_sources.last_error IS
    'Most recent fetch/parsing error message for source health diagnostics';
