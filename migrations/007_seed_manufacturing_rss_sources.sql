-- Migration 007: Seed 5 manufacturing RSS sources
-- Story: db-007 - 5 manufacturing RSS sources seeded

-- Insert 5 manufacturing industry RSS feed sources
INSERT INTO blog_rss_sources (name, url, category, active, priority) VALUES
('Assembly Magazine', 'https://www.assemblymag.com/rss/17', 'Manufacturing', true, 9),
('Manufacturing Dive', 'https://www.manufacturingdive.com/feeds/news', 'Manufacturing', true, 10),
('Modern Machine Shop', 'https://www.mmsonline.com/rss', 'Machining', true, 8),
('The Fabricator', 'https://www.thefabricator.com/rss/the-fabricator', 'Metal Fabrication', true, 7),
('American Machinist', 'https://www.americanmachinist.com/rss', 'Machining', true, 8)
ON CONFLICT (url) DO NOTHING;
