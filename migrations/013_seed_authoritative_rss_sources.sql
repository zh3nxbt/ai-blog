-- Migration 013: Improve RSS source quality with authoritative feeds
-- Task: data-quality
-- Description:
--   1) Disable fragile proxy/broken feeds
--   2) Add authoritative government/economic feeds relevant to manufacturing

-- Disable fragile/unofficial feeds that have proven unreliable.
UPDATE blog_rss_sources
SET active = false
WHERE url IN (
    'https://rsshub.app/apnews/topics/business',
    'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best'
);

-- Seed authoritative feeds.
INSERT INTO blog_rss_sources (name, url, category, active, priority) VALUES
(
    'Statistics Canada - The Daily (Manufacturing)',
    'https://www150.statcan.gc.ca/n1/rss/dai-quo/16-eng.atom',
    'Canadian Manufacturing Data',
    true,
    10
),
(
    'Statistics Canada - The Daily (International Trade)',
    'https://www150.statcan.gc.ca/n1/rss/dai-quo/12-eng.atom',
    'Canadian Trade Policy',
    true,
    10
),
(
    'Canada Gazette Part II (Official Regulations)',
    'https://www.gazette.gc.ca/rss/p2-eng.xml',
    'Government Regulations',
    true,
    10
),
(
    'Canada Gazette Part I (Notices & Proposed Regulations)',
    'https://www.gazette.gc.ca/rss/p1-eng.xml',
    'Government Notices',
    true,
    9
),
(
    'BLS Productivity and Costs',
    'https://www.bls.gov/feed/prod2.rss',
    'US Economic Indicators',
    true,
    8
),
(
    'BLS Manufacturing Productivity by Industry',
    'https://www.bls.gov/feed/prin.rss',
    'US Manufacturing Data',
    true,
    8
)
ON CONFLICT (url) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    active = EXCLUDED.active,
    priority = EXCLUDED.priority;
