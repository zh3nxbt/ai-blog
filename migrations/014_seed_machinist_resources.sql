-- Migration 014: Seed high-signal machinist/manufacturing resources
-- Task: data-quality
-- Description:
--   1) Add authoritative RSS feeds for regulations, standards, and manufacturing programs
--   2) Seed curated standards + evergreen resources for machinists and production engineers

-- Add/refresh authoritative RSS feeds.
INSERT INTO blog_rss_sources (name, url, category, active, priority) VALUES
(
    'NIST Manufacturing Innovation Blog',
    'https://www.nist.gov/blogs/manufacturing-innovation-blog/rss.xml',
    'Manufacturing Innovation',
    true,
    10
),
(
    'NIST News',
    'https://www.nist.gov/news-events/news.xml',
    'Standards & Metrology',
    true,
    8
),
(
    'U.S. Federal Register (GovInfo)',
    'https://www.govinfo.gov/rss/fr.xml',
    'Government Regulations',
    true,
    9
),
(
    'Code of Federal Regulations Updates (GovInfo)',
    'https://www.govinfo.gov/rss/cfr.xml',
    'Government Regulations',
    true,
    7
),
(
    'OSHA News Releases',
    'https://www.osha.gov/rss/newsreleases.xml',
    'Workplace Safety',
    true,
    8
),
(
    'OSHA Federal Register Notices',
    'https://www.osha.gov/rss/fedreg.xml',
    'Workplace Safety',
    true,
    9
),
(
    'OSHA Directives',
    'https://www.osha.gov/rss/directives.xml',
    'Safety Guidance',
    true,
    8
),
(
    'OSHA Letters of Interpretation',
    'https://www.osha.gov/rss/interps.xml',
    'Safety Guidance',
    true,
    7
)
ON CONFLICT (url) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    active = EXCLUDED.active,
    priority = EXCLUDED.priority;

-- Seed curated topic sources and items for standards + evergreen playbooks.
WITH seed_sources AS (
    SELECT * FROM (
        VALUES
            (
                'standards',
                'OSHA Machine Shop Standards Library',
                'Safety & Compliance',
                true,
                10,
                'Curated OSHA standards pages relevant to machining and fabrication operations.'
            ),
            (
                'standards',
                'NIST Manufacturing Improvement Library',
                'Process Control & Metrology',
                true,
                9,
                'Curated NIST resources for manufacturing improvement, measurement, and engineering practice.'
            ),
            (
                'evergreen',
                'Production Engineering Evergreen Bank',
                'Manufacturing Operations',
                true,
                8,
                'Evergreen production-line and machine-shop playbooks for reliable repeatable output.'
            )
    ) AS t(source_type, name, category, active, priority, notes)
),
inserted_sources AS (
    INSERT INTO blog_topic_sources (source_type, name, category, active, priority, notes)
    SELECT
        seed_sources.source_type,
        seed_sources.name,
        seed_sources.category,
        seed_sources.active,
        seed_sources.priority,
        seed_sources.notes
    FROM seed_sources
    WHERE NOT EXISTS (
        SELECT 1
        FROM blog_topic_sources existing
        WHERE existing.source_type = seed_sources.source_type
          AND existing.name = seed_sources.name
    )
    RETURNING id, source_type, name
),
all_sources AS (
    SELECT id, source_type, name FROM inserted_sources
    UNION ALL
    SELECT existing.id, existing.source_type, existing.name
    FROM blog_topic_sources existing
    JOIN seed_sources
      ON existing.source_type = seed_sources.source_type
     AND existing.name = seed_sources.name
),
seed_items AS (
    SELECT * FROM (
        VALUES
            (
                'OSHA Machine Shop Standards Library',
                'Machine Guarding Requirements for Shop Equipment',
                'Baseline guarding requirements for mills, lathes, drills, and CNC equipment under 29 CFR 1910.212.',
                'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.212'
            ),
            (
                'OSHA Machine Shop Standards Library',
                'Mechanical Power-Transmission Guarding',
                'What OSHA expects for belts, pulleys, shafts, and moving drive elements under 29 CFR 1910.219.',
                'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.219'
            ),
            (
                'OSHA Machine Shop Standards Library',
                'Lockout/Tagout for Maintenance and Setup',
                'Control of hazardous energy requirements for setup, troubleshooting, and maintenance on machine tools.',
                'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147'
            ),
            (
                'OSHA Machine Shop Standards Library',
                'PPE Program Requirements for Fabrication Shops',
                'How to structure hazard assessments and PPE selection for grinding, cutting, and machining tasks.',
                'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.132'
            ),
            (
                'OSHA Machine Shop Standards Library',
                'Occupational Noise Exposure Controls',
                'Requirements and practical thresholds for hearing conservation in production environments.',
                'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.95'
            ),
            (
                'OSHA Machine Shop Standards Library',
                'Abrasive Wheel Machinery Safety',
                'Guarding, ring testing, and operating requirements for bench grinders and abrasive wheel equipment.',
                'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.215'
            ),
            (
                'OSHA Machine Shop Standards Library',
                'Welding, Cutting, and Brazing Safety Basics',
                'Ventilation, fire prevention, and safe work controls for fabrication and weld operations.',
                'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.252'
            ),
            (
                'NIST Manufacturing Improvement Library',
                'NIST Manufacturing Extension Partnership Overview',
                'Program overview and support model for small and midsize manufacturers improving process capability.',
                'https://www.nist.gov/mep'
            ),
            (
                'NIST Manufacturing Improvement Library',
                'NIST Advanced Manufacturing Program',
                'Cross-lab manufacturing program work including measurement science and interoperability priorities.',
                'https://www.nist.gov/programs-projects/advanced-manufacturing-program'
            ),
            (
                'NIST Manufacturing Improvement Library',
                'NIST Engineering Laboratory',
                'Applied engineering research areas that impact dimensional control, automation, and production quality.',
                'https://www.nist.gov/engineering-laboratory'
            ),
            (
                'Production Engineering Evergreen Bank',
                'Using Cp and Cpk before lights-out production',
                'How to set capability targets and sampling plans before approving unattended production runs.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'First-article checks vs in-process control plans',
                'Where first-article inspection ends and process control must take over to avoid drift.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Gage R&R setup for shop-floor measurement',
                'A practical repeatability and reproducibility plan for micrometers, bore gages, and CMM checks.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'PFMEA for fixture and tooling changes',
                'Using process FMEA to de-risk fixture redesigns, tool substitutions, and handoff to production.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'SPC reaction plans that operators can follow',
                'How to define clear stop-adjust-escalate actions when control charts signal instability.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Managing tool life offsets across shifts',
                'Methods for shift-to-shift offset governance to keep dimensions centered and scrap predictable.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Prove-out to production handoff checklist',
                'A handoff checklist that captures feeds, speeds, offsets, fixtures, and quality gates.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Setup reduction with modular fixturing',
                'How modular fixturing reduces changeover time without sacrificing repeatability.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Fixture repeatability qualification method',
                'A simple qualification protocol for confirming clamp repeatability before release.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Cycle-time decomposition for bottleneck control',
                'Break cycle time into cut, toolchange, handling, and wait states to target high-payoff fixes.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Scrap Pareto and containment loop',
                'How to run weekly Pareto reviews and immediate containment for top recurring defects.',
                NULL
            ),
            (
                'Production Engineering Evergreen Bank',
                'Layered process audits for machine cells',
                'Lightweight layered audits that catch setup drift before parts go out of tolerance.',
                NULL
            )
    ) AS t(source_name, title, summary, url)
)
INSERT INTO blog_topic_items (source_id, title, summary, url, metadata)
SELECT
    all_sources.id,
    seed_items.title,
    seed_items.summary,
    seed_items.url,
    jsonb_build_object(
        'seed_migration', '014',
        'resource_kind', CASE
            WHEN seed_items.url IS NULL THEN 'evergreen_playbook'
            ELSE 'specialized_page'
        END
    )
FROM seed_items
JOIN all_sources ON all_sources.name = seed_items.source_name
WHERE NOT EXISTS (
    SELECT 1
    FROM blog_topic_items existing
    WHERE existing.source_id = all_sources.id
      AND existing.title = seed_items.title
);
