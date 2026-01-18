-- Migration 012: Seed trade and policy RSS sources
-- Task: Improve RSS news selection with major news priority
-- Description: Add RSS feeds focused on trade policy, supply chain, and business news

-- Insert trade/policy-focused RSS feed sources
-- Uses ON CONFLICT to skip any duplicates
INSERT INTO blog_rss_sources (name, url, category, active, priority) VALUES
('Supply Chain Dive', 'https://www.supplychaindive.com/feeds/news/', 'Supply Chain', true, 9),
('Industry Week', 'https://www.industryweek.com/rss', 'Manufacturing News', true, 9),
('Reuters Business', 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best', 'Business News', true, 10),
('AP Business News', 'https://rsshub.app/apnews/topics/business', 'Business News', true, 10)
ON CONFLICT (url) DO NOTHING;
