"""Content strategy screening prompt for determining the best approach for a given source pool."""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


class ContentStrategy(Enum):
    """Content generation strategy based on source pool characteristics."""

    ANCHOR_CONTEXT = "anchor_context"  # One dominant story + supporting context
    THEMATIC = "thematic"  # Multiple sources on same theme
    ANALYSIS = "analysis"  # Scattered sources tied by shop-floor perspective
    DEEP_DIVE = "deep_dive"  # 1-2 sources with deeper treatment


@dataclass
class StrategyScreeningResult:
    """Result of content strategy screening."""

    strategy: ContentStrategy
    strategy_reason: str
    anchor_item_index: Optional[int]  # For ANCHOR_CONTEXT
    theme_clusters: Dict[str, List[int]]  # theme_name -> item indices
    recommended_indices: List[int]  # Which items to use
    items_with_scores: List[Dict[str, Any]]
    cost_cents: int


STRATEGY_SCREENING_PROMPT_TEMPLATE = """Analyze these source items for a precision manufacturing blog and recommend a content strategy.

**IMPORTANT CONTEXT:**
This blog is for a machine shop based in Ontario, Canada. Content should be:
- Relevant to Canadian manufacturers, OR
- Globally applicable (technical topics, best practices, industry trends)
- US-specific policy/regulations are LOWER priority unless they directly impact Canadian operations (e.g., cross-border trade, tariffs affecting Canada)

**SOURCE ITEMS:**
{items_json}

**YOUR TASK:**
1. Score each item for newsworthiness (urgency_score 0.0-1.0)
2. Identify themes that connect multiple items
3. Recommend the best content strategy

**STRATEGY OPTIONS:**

1. **anchor_context** - Use when ONE item clearly dominates (urgency >= 0.8)
   - That item becomes the main story
   - Other items provide supporting context only
   - Result: Focused post with clear narrative

2. **thematic** - Use when 2+ items share a common theme
   - Group related items together
   - Ignore unrelated items
   - Result: Cohesive post exploring one topic from multiple angles

3. **analysis** - Use when items are scattered but individually solid
   - Find a unifying "shop floor perspective" angle
   - What do these mean for a machine shop owner?
   - Result: Commentary/analysis piece tying disparate news together

4. **deep_dive** - Use when source pool is weak OR one item deserves thorough treatment
   - Pick only 1-2 best items
   - Go deeper rather than broader
   - Result: In-depth exploration of a single topic

**URGENCY SCORING:**
- 0.9-1.0: Breaking news - immediate impact on manufacturing operations
- 0.7-0.9: Important development - significant industry implications
- 0.5-0.7: Notable but routine - worth covering, not urgent
- 0.0-0.5: Low value - filler content

**THEME IDENTIFICATION:**
Look for connections like:
- Same material/process (aluminum, CNC, coating, etc.)
- Same business concern (costs, supply chain, regulations)
- Same industry segment (aerospace, medical, automotive)
- Same type of development (new tech, policy change, market shift)

**OUTPUT FORMAT (JSON ONLY):**
{{
  "item_scores": [
    {{
      "item_index": 0,
      "urgency_score": 0.0-1.0,
      "themes": ["theme1", "theme2"],
      "summary": "One line describing item's value"
    }}
  ],
  "theme_clusters": {{
    "theme_name": [0, 2, 4],
    "another_theme": [1, 3]
  }},
  "strategy": "anchor_context|thematic|analysis|deep_dive",
  "strategy_reason": "Brief explanation of why this strategy fits",
  "anchor_index": null or integer (only for anchor_context),
  "recommended_indices": [0, 2, 4],
  "unifying_angle": "For analysis strategy: the shop-floor perspective that ties items together"
}}

Be decisive. Pick the strategy that will produce the most valuable, coherent blog post.
"""
