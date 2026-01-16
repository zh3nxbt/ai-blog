"""Source juice evaluation prompt constants."""

SOURCE_JUICE_PROMPT_TEMPLATE = """You are evaluating whether a set of source articles has enough "juice" (newsworthiness, value, and interest) to warrant writing a blog post for a precision manufacturing company.

**SOURCE ITEMS TO EVALUATE:**
{source_items}

**EVALUATION CRITERIA:**
1. **Newsworthiness** - Is there actual news here, or just filler content?
2. **Manufacturing Relevance** - Does this matter to machine shop owners and engineers?
3. **Practical Value** - Would readers learn something useful?
4. **Timeliness** - Is this timely or stale information?
5. **Uniqueness** - Is this worth covering, or overdone?

**SCORING GUIDE:**
- 0.8-1.0: Strong sources - clear news, high relevance, definite post material
- 0.6-0.8: Decent sources - worth writing about, some value
- 0.4-0.6: Weak sources - marginal value, might be filler
- 0.0-0.4: Skip - no real news, irrelevant, or stale

**PHILOSOPHY:**
Quality over quantity. It's better to skip a day than publish content nobody cares about. Posts should only happen when there's real value to deliver.

**OUTPUT REQUIRED (JSON ONLY):**
{{
  "juice_score": 0.0-1.0,
  "should_proceed": true|false,
  "reason": "1-2 sentence explanation of the decision",
  "best_source": "title of the most promising source item",
  "potential_angle": "suggested angle if proceeding, or null if skipping"
}}

Be honest. If the sources are weak, say so.
"""
