-- Migration: Seed evergreen topic bank
-- Task: mix-002
-- Description: Seed evergreen topics into blog_topic_items

WITH existing_source AS (
    SELECT id
    FROM blog_topic_sources
    WHERE source_type = 'evergreen'
      AND name = 'Evergreen Topic Bank'
),
inserted_source AS (
    INSERT INTO blog_topic_sources (source_type, name, category, priority, notes)
    SELECT 'evergreen', 'Evergreen Topic Bank', 'evergreen', 5, 'Seeded evergreen topics for Ralph'
    WHERE NOT EXISTS (SELECT 1 FROM existing_source)
    RETURNING id
),
source_id AS (
    SELECT id FROM inserted_source
    UNION ALL
    SELECT id FROM existing_source
),
seed_items AS (
    SELECT * FROM (
        VALUES
            (
                '6061 vs 7075: picking aluminum that machines clean',
                'Highlights strength, corrosion resistance, and chip control differences that affect cycle time and scrap.'
            ),
            (
                'Tolerance stacking in assemblies',
                'Shows how small deviations add up across parts and where to place tighter controls to avoid rework.'
            ),
            (
                'Tool wear indicators and replacement timing',
                'Covers flank wear, chipping, and surface finish signals that it is time to change inserts.'
            ),
            (
                'Coolant concentration checks that prevent rust and odor',
                'Explains simple refractometer checks and how mix ratios affect tool life and part finish.'
            ),
            (
                'Deburring small parts without rounding edges',
                'Compares hand, brush, and abrasive methods to remove burrs while protecting sharp features.'
            ),
            (
                'Surface finish and fatigue life',
                'Connects Ra values to crack initiation and when a smoother finish pays for itself.'
            ),
            (
                'Heat treating 4140 vs 4340 for strength',
                'Summarizes hardness ranges, distortion risks, and when each alloy is the safer choice.'
            ),
            (
                'Fixturing thin-wall parts',
                'Discusses soft jaws, support ribs, and clamping strategies that avoid ovality.'
            ),
            (
                'Tap drill sizing and thread engagement',
                'Explains percentage of thread and why chasing maximum engagement can break taps.'
            ),
            (
                'Burr control in cross-hole drilling',
                'Outlines drill order, backing material, and deburr tools that keep intersections clean.'
            ),
            (
                'EDM vs milling for tight internal corners',
                'Compares corner radii, cost, and lead time for sharp internal features.'
            ),
            (
                'GD&T: position vs profile',
                'Clarifies where each tolerance applies and how they affect inspection setups.'
            ),
            (
                'Preventing chatter in end milling',
                'Explains chip load, stickout, and toolpath tweaks that stabilize the cut.'
            ),
            (
                'Carbide vs HSS in production machining',
                'Breaks down speed limits, toughness, and cost per part for each tool material.'
            ),
            (
                'Measuring flatness with a granite plate',
                'Walks through indicator sweeps and common mistakes that hide high spots.'
            ),
            (
                'Chip evacuation in deep-hole drilling',
                'Details peck cycles, coolant pressure, and flute choices that prevent packing.'
            ),
            (
                'Why climb milling reduces tool wear',
                'Explains rubbing vs shearing and when conventional milling still makes sense.'
            ),
            (
                'Toolholder runout and its impact on finish',
                'Shows how a few tenths of runout raises tool load and leaves witness marks.'
            ),
            (
                'Selecting reamers for tight tolerance holes',
                'Compares straight vs spiral flute and how stock allowance drives final size.'
            ),
            (
                'Balancing cutting speed and feed rate',
                'Links chip thickness to heat and explains how to adjust without losing size control.'
            ),
            (
                'Insert grades for steel vs stainless',
                'Summarizes coating choices and edge prep that handle heat and work hardening.'
            ),
            (
                'Managing thermal growth on long runs',
                'Covers warm-up parts, offset tracking, and in-process gaging.'
            ),
            (
                'Part marking for traceability',
                'Compares laser, dot peen, and ink methods for durability and legibility.'
            ),
            (
                'Calibration schedules that prevent surprises',
                'Outlines which gages need daily checks and what can run on quarterly cycles.'
            ),
            (
                'DFM checklist for machinists',
                'Lists quick questions that catch hard-to-machine features before quoting.'
            )
    ) AS seed(title, summary)
)
INSERT INTO blog_topic_items (source_id, title, summary)
SELECT source_id.id, seed_items.title, seed_items.summary
FROM source_id, seed_items
WHERE NOT EXISTS (
    SELECT 1
    FROM blog_topic_items existing
    WHERE existing.source_id = source_id.id
      AND existing.title = seed_items.title
);
