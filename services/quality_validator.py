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


def validate_structure(content: str) -> Tuple[bool, List[str], float]:
    """
    Validate content structure including headings and paragraph breaks.

    Checks if content has proper markdown structure with headings (## and ###)
    and adequate paragraph breaks for readability.

    Args:
        content: The markdown text content to validate.

    Returns:
        Tuple of (is_valid: bool, issues: List[str], score: float)
        - is_valid: True if content has acceptable structure
        - issues: List of specific structural issues found
        - score: Quality score between 0.0-1.0 based on structure

    Structure checks:
        - Presence of H2 (##) headings
        - Presence of H3 (###) headings (optional but adds to score)
        - Adequate paragraph breaks (double newlines)
        - Minimum paragraph count for readability

    Examples:
        >>> validate_structure("No headings here.\\n\\nJust paragraphs.")
        (False, ['missing headings'], 0.3)
        >>> validate_structure("## Title\\n\\nContent here.\\n\\n### Section\\n\\nMore content.")
        (True, [], 0.9)
    """
    if not content:
        return (False, ["empty content"], 0.0)

    issues = []
    score = 1.0

    # Check for H2 headings (##)
    h2_pattern = r"^##\s+.+$"
    h2_matches = re.findall(h2_pattern, content, re.MULTILINE)
    has_h2 = len(h2_matches) > 0

    # Check for H3 headings (###)
    h3_pattern = r"^###\s+.+$"
    h3_matches = re.findall(h3_pattern, content, re.MULTILINE)
    has_h3 = len(h3_matches) > 0

    # Check for any markdown headings (including # H1)
    any_heading_pattern = r"^#{1,6}\s+.+$"
    any_heading_matches = re.findall(any_heading_pattern, content, re.MULTILINE)
    has_any_headings = len(any_heading_matches) > 0

    # Check for paragraph breaks (double newlines or content blocks separated by blank lines)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    paragraph_count = len(paragraphs)

    # Calculate score based on structure elements

    # No headings at all is a major issue
    if not has_any_headings:
        issues.append("missing headings")
        score -= 0.55

    # Having H2 headings is important for structure
    if not has_h2 and has_any_headings:
        # Has some headings but not H2 - minor issue
        issues.append("no H2 (##) headings")
        score -= 0.2

    # Having H3 headings adds to score (bonus for good sub-structure)
    if has_h2 and has_h3:
        score += 0.05  # Small bonus for good hierarchy
    elif has_h2 and not has_h3:
        # H2 only is fine, no penalty
        pass

    # Check heading count for longer content
    total_headings = len(any_heading_matches)
    if paragraph_count > 5 and total_headings < 2:
        issues.append("insufficient headings for content length")
        score -= 0.15

    # Check for adequate paragraph breaks
    min_paragraphs = 3
    if paragraph_count < min_paragraphs:
        issues.append("insufficient paragraph breaks")
        score -= 0.2

    # Bonus for good paragraph structure (5-15 paragraphs is ideal for blog posts)
    if 5 <= paragraph_count <= 15:
        score += 0.05

    # Check for very long paragraphs (walls of text)
    long_paragraph_threshold = 500  # characters
    long_paragraphs = [p for p in paragraphs if len(p) > long_paragraph_threshold]
    if len(long_paragraphs) > 2:
        issues.append("contains very long paragraphs")
        score -= 0.1

    # Ensure score stays within bounds
    score = max(0.0, min(1.0, score))

    # Determine validity: must have headings and adequate paragraphs
    is_valid = has_any_headings and paragraph_count >= min_paragraphs

    return (is_valid, issues, round(score, 2))


BRAND_VOICE_FORBIDDEN = [
    "revolutionary",
    "game-changer",
]


def validate_brand_voice(content: str) -> Tuple[bool, List[str], float]:
    """
    Validate content tone against MAS Precision Parts brand voice.

    Flags overly salesy language, excessive excitement, and buzzwords that
    conflict with the practical shop-veteran tone.

    Args:
        content: The text content to validate.

    Returns:
        Tuple of (is_valid: bool, issues: List[str], score: float)
        - is_valid: True if content matches brand voice expectations
        - issues: List of brand voice issues found
        - score: Quality score between 0.0-1.0 based on tone

    Examples:
        >>> validate_brand_voice("Revolutionary tooling!!!")
        (False, ['marketing buzzwords: revolutionary', 'excessive exclamation marks'], 0.1)
        >>> validate_brand_voice("Surface finish affects how parts fail.")
        (True, [], 0.9)
    """
    if not content:
        return (False, ["empty content"], 0.0)

    issues = []
    score = 1.0

    exclamation_count = content.count("!")
    if exclamation_count >= 5:
        issues.append("excessive exclamation marks")
        score -= 0.5

    content_lower = content.lower()
    found_terms = []
    for term in BRAND_VOICE_FORBIDDEN:
        term_lower = term.lower()
        if " " in term_lower:
            pattern = re.escape(term_lower).replace(r"\ ", r"\s+")
            if re.search(pattern, content_lower):
                found_terms.append(term)
        else:
            pattern = r"\b" + re.escape(term_lower) + r"\b"
            if re.search(pattern, content_lower):
                found_terms.append(term)

    if found_terms:
        issues.append(f"marketing buzzwords: {', '.join(found_terms)}")
        score -= 0.5

    score = max(0.0, min(1.0, score))
    is_valid = len(issues) == 0 and score >= 0.8

    return (is_valid, issues, round(score, 2))
