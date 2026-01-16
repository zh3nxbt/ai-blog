-- Migration 010: Seed expanded manufacturing RSS sources
-- Story: db-008 - Seed expanded manufacturing RSS sources (Canada/Ontario focus)
-- Source: ralph/rss_sources_canada.csv

-- Insert 40 additional manufacturing industry RSS feed sources
-- Uses ON CONFLICT to skip any duplicates
INSERT INTO blog_rss_sources (name, url, category, active, priority) VALUES
('Aerospace Manufacturing Magazine', 'https://www.aero-mag.com/feed/', 'Aerospace', true, 8),
('Automation World RSS Feed', 'https://www.automationworld.com/rss.xml', 'Automation & Controls', true, 8),
('BroadCaster Magazine (Canada) Headline News', 'https://broadcastermagazine.com/rssfeeds/BM_dailynews.xml', 'Canadian Industry News', true, 6),
('Canadian Manufacturing Daily Brief', 'https://www.canadianmanufacturing.com/rss', 'Manufacturing News', true, 9),
('Canadian Metalworking', 'https://canadianmetalworking.com/meter/rss', 'Metalworking', true, 6),
('CNC Cookbook Blog', 'https://www.cnccookbook.com/feed', 'CNC Machining', true, 8),
('CNC Masters', 'https://www.cncmasters.com/feed/', 'Machining', true, 6),
('CNC WEST', 'https://cnc-west.com/feed/', 'Machining', true, 7),
('Datron Dynamics', 'https://www.datron.com/feed/', 'Machining', true, 7),
('Fabricating & Metalworking', 'https://fabricatingandmetalworking.com/feed/', 'Metalworking', true, 8),
('FMA Blog (Fabricators & Manufacturers Association)', 'https://fmamfg.org/blog/rss.xml', 'Industry Assoc Blog', true, 7),
('In the Loupe (Harvey Performance)', 'https://www.harveyperformance.com/feed/', 'Machining', true, 8),
('Industrial Distribution', 'https://www.inddist.com/rss', 'Supply Chain', true, 7),
('Laguna Tools Blog', 'https://info.lagunatools.com/rss.xml', 'Machining', true, 7),
('Mantech Machinery', 'https://www.mantechmachinery.co.uk/feed/', 'Manufacturing', true, 6),
('Manufacturing & Engineering News (EIN)', 'https://manufacturing.einnews.com/all_rss', 'Manufacturing News', true, 8),
('Manufacturing.net', 'https://www.manufacturing.net/rss33.xml', 'Manufacturing', true, 8),
('ManufacturingTomorrow CNC', 'https://www.manufacturingtomorrow.com/tag/cnc/rss', 'Manufacturing/CNC', true, 6),
('Mastercam Blog', 'https://www.mastercam.com/news/blog/feed/', 'CAD/CAM', true, 8),
('Medical Design & Outsourcing', 'http://feeds.feedburner.com/MedicalDesignAndOutsourcing', 'Medical Manufacturing', true, 8),
('MetalForming Magazine', 'https://metalformingmagazine.com/articles/rss', 'Metal Forming', true, 8),
('Metalworking News', 'https://metalworkingnews.info/feed', 'Metalworking', true, 7),
('Metalworking World Magazine', 'https://metalworkingworldmagazine.com/feed', 'Metal Fabrication', true, 7),
('Methods Machine Tools News', 'https://www.methodsmachine.com/news/rss', 'Company & Tech News', true, 5),
('NTMA (National Tooling and Machining Association)', 'https://ntma.org/feed/', 'Machining', true, 9),
('OneCNC News', 'https://www.onecnc.net/en/feed/', 'CAD/CAM', true, 7),
('Plant Services', 'https://www.plantservices.com/rss', 'Maintenance', true, 8),
('PMPA (Precision Machined Products Association)', 'https://www.pmpa.org/feed/', 'Precision Machining', true, 9),
('Practical Machinist', 'https://www.practicalmachinist.com/feed/', 'Machining', true, 10),
('Quality Digest', 'https://www.qualitydigest.com/rss.xml', 'Quality Assurance', true, 7),
('Quality Magazine', 'https://www.qualitymag.com/rss/articles', 'Quality Assurance', true, 8),
('Robotics & Automation News (UK)', 'https://roboticsandautomationnews.co.uk/rss', 'Automation & Robotics', true, 7),
('Robotics & Automation News', 'https://roboticsandautomationnews.com/feed', 'Industrial Robotics', true, 8),
('Shop Metalworking Technology', 'https://www.shopmetaltech.com/feed', 'Machining/Metalworking', true, 9),
('SME Advanced Manufacturing Now', 'https://advmn.libsyn.com/rss', 'Manufacturing', true, 9),
('The Robot Report', 'https://www.therobotreport.com/feed', 'Industrial Robotics', true, 9),
('Thomas Industry Update Blog', 'https://blog.thomasnet.com/feed', 'Manufacturing (General)', true, 7),
('Today''s Machining World', 'https://todaysmachiningworld.com/feed/', 'Machining', true, 9),
('Tormach Blog', 'https://www.tormach.com/articles/rss.xml', 'Machining', true, 7),
('Welding Tips and Tricks', 'https://wttpodcast.libsyn.com/rss', 'Welding', true, 7)
ON CONFLICT (url) DO NOTHING;
