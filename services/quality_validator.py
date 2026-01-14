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


# Length validation constants
MIN_WORDS = 1000
MAX_WORDS = 2500
IDEAL_MIN_WORDS = 1200
IDEAL_MAX_WORDS = 2000


def count_words(content: str) -> int:
    """
    Count the number of words in content.

    Words are defined as sequences of non-whitespace characters.

    Args:
        content: The text content to count words in.

    Returns:
        Integer count of words in the content.
    """
    if not content:
        return 0
    return len(content.split())


def validate_length(content: str) -> Tuple[bool, int, float]:
    """
    Validate content length against target word count range.

    Checks if content falls within the acceptable word count range of 1000-2500 words.
    Content in the ideal range (1200-2000 words) gets the highest scores.

    Args:
        content: The text content to validate.

    Returns:
        Tuple of (is_valid: bool, word_count: int, score: float)
        - is_valid: True if word count is within 1000-2500 range
        - word_count: The actual word count
        - score: Quality score between 0.0-1.0 based on length

    Score calculation:
        - Under 500 words: score scales from 0.0 to 0.3
        - 500-1000 words: score scales from 0.3 to 0.7
        - 1000-1200 words: score scales from 0.7 to 0.9
        - 1200-2000 words: score is 0.9-1.0 (ideal range)
        - 2000-2500 words: score scales from 0.9 to 0.7
        - 2500-3500 words: score scales from 0.7 to 0.4
        - Over 3500 words: score scales down from 0.4

    Examples:
        >>> validate_length("short " * 500)  # 500 words
        (False, 500, 0.3)
        >>> validate_length("good " * 1500)  # 1500 words
        (True, 1500, 0.95)
        >>> validate_length("long " * 3000)  # 3000 words
        (False, 3000, 0.55)
    """
    word_count = count_words(content)

    # Determine if valid (within 1000-2500 range)
    is_valid = MIN_WORDS <= word_count <= MAX_WORDS

    # Calculate score based on word count
    if word_count == 0:
        score = 0.0
    elif word_count < 500:
        # Very short: 0.0 to 0.3
        score = (word_count / 500) * 0.3
    elif word_count < MIN_WORDS:
        # Short (500-1000): 0.3 to 0.7
        progress = (word_count - 500) / 500
        score = 0.3 + progress * 0.4
    elif word_count < IDEAL_MIN_WORDS:
        # Acceptable but not ideal (1000-1200): 0.7 to 0.9
        progress = (word_count - MIN_WORDS) / (IDEAL_MIN_WORDS - MIN_WORDS)
        score = 0.7 + progress * 0.2
    elif word_count <= IDEAL_MAX_WORDS:
        # Ideal range (1200-2000): 0.9 to 1.0
        progress = (word_count - IDEAL_MIN_WORDS) / (IDEAL_MAX_WORDS - IDEAL_MIN_WORDS)
        score = 0.9 + progress * 0.1
    elif word_count <= MAX_WORDS:
        # Acceptable but long (2000-2500): 0.9 to 0.7
        progress = (word_count - IDEAL_MAX_WORDS) / (MAX_WORDS - IDEAL_MAX_WORDS)
        score = 0.9 - progress * 0.2
    elif word_count <= 3500:
        # Too long (2500-3500): 0.7 to 0.4
        progress = (word_count - MAX_WORDS) / 1000
        score = 0.7 - progress * 0.3
    else:
        # Very long (>3500): 0.4 and decreasing
        excess = word_count - 3500
        score = max(0.1, 0.4 - (excess / 2000) * 0.3)

    return (is_valid, word_count, round(score, 2))
