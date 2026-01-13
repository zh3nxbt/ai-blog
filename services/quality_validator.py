"""Quality validation functions for blog content.

This module provides functions to detect AI-generated content patterns
and validate content quality for the MAS Precision Parts blog.
"""

import re
from typing import List, Tuple


# Forbidden AI slop keywords and phrases that should never appear in published content.
# Single words use word boundary matching, phrases match exactly.
AI_SLOP_KEYWORDS = [
    # Single words
    "delve",
    "unveil",
    "landscape",
    "realm",
    "unlock",
    "leverage",
    "utilize",
    "robust",
    "streamline",
    "cutting-edge",
    "revolutionary",
    "harness",
    "paradigm",
    "synergy",
    "game-changer",
    # Phrases (matched with flexible whitespace)
    "in today's fast-paced world",
    "it's important to note",
    "let's explore",
    "dive deep",
    "best practices",
]


def detect_ai_slop(content: str) -> Tuple[bool, List[str]]:
    """
    Detect AI slop keywords and phrases in content.

    Scans content for forbidden AI-generated language patterns that make
    content sound robotic or generic. Content containing these patterns
    should be penalized in quality scoring.

    Args:
        content: The text content to scan for AI slop patterns.

    Returns:
        Tuple of (has_slop: bool, found_keywords: List[str])
        - has_slop: True if any forbidden keywords/phrases were found
        - found_keywords: List of specific keywords/phrases that were detected

    Examples:
        >>> detect_ai_slop("Let us delve into the topic")
        (True, ['delve'])
        >>> detect_ai_slop("We leverage this technology")
        (True, ['leverage'])
        >>> detect_ai_slop("Simple plain text about machining")
        (False, [])
    """
    if not content:
        return (False, [])

    # Normalize content for matching
    content_lower = content.lower()
    found_keywords = []

    for keyword in AI_SLOP_KEYWORDS:
        keyword_lower = keyword.lower()

        # For multi-word phrases, use flexible whitespace matching
        if " " in keyword_lower:
            # Replace spaces with regex pattern that matches any whitespace
            pattern = re.escape(keyword_lower).replace(r"\ ", r"\s+")
            if re.search(pattern, content_lower):
                found_keywords.append(keyword)
        else:
            # For single words, use word boundary matching to avoid false positives
            # e.g., "landscape" shouldn't match "landscapes" substring in middle of word
            pattern = r"\b" + re.escape(keyword_lower) + r"\b"
            if re.search(pattern, content_lower):
                found_keywords.append(keyword)

    has_slop = len(found_keywords) > 0
    return (has_slop, found_keywords)
