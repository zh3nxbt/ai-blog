"""Major news screening prompt for identifying high-priority RSS items."""

MAJOR_NEWS_SCREENING_PROMPT_TEMPLATE = """Evaluate these RSS items and identify any that qualify as "major news" for a precision manufacturing company's blog.

**RSS ITEMS TO SCREEN:**
{items_json}

**MAJOR NEWS CRITERIA:**
A story qualifies as major news if it has ANY of these characteristics:
1. **Trade policy changes** - Tariffs, trade agreements, sanctions, import/export regulations
2. **Major industry events** - Significant acquisitions, bankruptcies, plant closures/openings
3. **Government regulations** - New manufacturing standards, safety requirements, environmental rules
4. **Supply chain disruptions** - Material shortages, logistics issues, supplier problems
5. **Significant economic data** - Major manufacturing indices, employment data, commodity prices

**URGENCY SCORING:**
- 0.9-1.0: Breaking news - immediate impact on manufacturing operations or costs
- 0.7-0.9: Important development - significant industry implications
- 0.5-0.7: Notable but not urgent - worth covering but not time-sensitive
- 0.0-0.5: Routine news - no special priority needed

**OUTPUT FORMAT (JSON ONLY):**
{{
  "screening_results": [
    {{
      "item_index": 0,
      "is_major_news": true|false,
      "urgency_score": 0.0-1.0,
      "reason": "Brief explanation of why this is/isn't major news"
    }}
  ]
}}

Be selective. Most items should NOT be major news. Only flag genuinely significant developments.
"""
