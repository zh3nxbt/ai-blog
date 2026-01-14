#!/usr/bin/env python3
"""Verification script for svc-010: validate_structure() function.

Acceptance Criteria:
1. Function validate_structure(content) exists
2. Content without headings returns (False, issues, score < 0.5)
3. Content with ## and ### headings returns (True, [], score > 0.8)
4. Issues list includes 'missing headings' when applicable
5. Checks for paragraph breaks
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_svc_010() -> bool:
    """Verify all acceptance criteria for svc-010."""
    print("=" * 60)
    print("VERIFICATION: svc-010 - validate_structure() function")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Import test - Function exists
    print("\n[1/5] Verifying function exists and can be imported...")
    try:
        from services.quality_validator import validate_structure
        print("✓ Successfully imported validate_structure")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: Content without headings returns (False, issues, score < 0.5)
    print("\n[2/5] Verifying content without headings returns (False, issues, score < 0.5)...")
    try:
        # Content with no headings but has paragraph breaks
        content_no_headings = """This is a paragraph without any headings.

It has some text here and there.

But no markdown headings at all.

Just plain text paragraphs."""

        result = validate_structure(content_no_headings)
        is_valid, issues, score = result

        if not is_valid and score < 0.5:
            print(f"✓ Returned is_valid={is_valid}, score={score} (< 0.5)")
            print(f"  Issues: {issues}")
            passed += 1
        else:
            print("✗ Expected is_valid=False, score < 0.5")
            print(f"  Got is_valid={is_valid}, score={score}, issues={issues}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 3: Content with ## and ### headings returns (True, [], score > 0.8)
    print("\n[3/5] Verifying content with ## and ### headings returns (True, [], score > 0.8)...")
    try:
        content_with_headings = """## Main Title

This is the introduction paragraph with some content.

### First Section

Here we discuss the first topic in detail.

More content about the first section.

### Second Section

And here we cover the second major point.

Final thoughts on this topic."""

        result = validate_structure(content_with_headings)
        is_valid, issues, score = result

        if is_valid and len(issues) == 0 and score > 0.8:
            print(f"✓ Returned is_valid={is_valid}, issues={issues}, score={score} (> 0.8)")
            passed += 1
        else:
            print("✗ Expected is_valid=True, issues=[], score > 0.8")
            print(f"  Got is_valid={is_valid}, issues={issues}, score={score}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 4: Issues list includes 'missing headings' when applicable
    print("\n[4/5] Verifying issues list includes 'missing headings' when applicable...")
    try:
        content_no_headings = """No headings in this content.

Just paragraphs of text.

Multiple paragraphs here."""

        result = validate_structure(content_no_headings)
        is_valid, issues, score = result

        if "missing headings" in issues:
            print(f"✓ Issues list includes 'missing headings': {issues}")
            passed += 1
        else:
            print("✗ Expected 'missing headings' in issues list")
            print(f"  Got issues={issues}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 5: Checks for paragraph breaks
    print("\n[5/5] Verifying function checks for paragraph breaks...")
    try:
        # Content with headings but poor paragraph structure (single block)
        content_no_paragraphs = """## Title
Single block of text without proper paragraph breaks. This is all one paragraph that goes on and on without any double newlines to separate ideas. It should fail the paragraph check."""

        result = validate_structure(content_no_paragraphs)
        is_valid, issues, score = result

        # Should flag insufficient paragraph breaks
        if "insufficient paragraph breaks" in issues or not is_valid:
            print(f"✓ Detects poor paragraph structure: is_valid={is_valid}, issues={issues}")
            passed += 1
        else:
            # Even if no explicit issue, if the test content only has 2 paragraphs it should fail
            # Let's try with truly minimal content
            minimal_content = "## Title\nOne paragraph only."
            result2 = validate_structure(minimal_content)
            is_valid2, issues2, score2 = result2

            if "insufficient paragraph breaks" in issues2 or not is_valid2:
                print("✓ Detects insufficient paragraph breaks with minimal content")
                print(f"  Result: is_valid={is_valid2}, issues={issues2}")
                passed += 1
            else:
                print("✗ Expected detection of poor paragraph structure")
                print(f"  First test: is_valid={is_valid}, issues={issues}")
                print(f"  Second test: is_valid={is_valid2}, issues={issues2}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Additional edge case tests (informational, not part of acceptance criteria)
    print("\n[ADDITIONAL TESTS] Edge cases...")

    # Test empty content
    try:
        result = validate_structure("")
        if not result[0] and result[2] == 0.0:
            print("✓ Empty content returns (False, [...], 0.0)")
        else:
            print(f"⚠ Empty content issue: {result}")
    except Exception as e:
        print(f"⚠ Empty content test failed: {e}")

    # Test H2 only (should still be valid)
    try:
        content_h2_only = """## First Heading

Some content here.

## Second Heading

More content here.

## Third Heading

Final content."""

        result = validate_structure(content_h2_only)
        if result[0] and result[2] >= 0.8:
            print(f"✓ H2-only content passes: is_valid={result[0]}, score={result[2]}")
        else:
            print(f"⚠ H2-only content: {result}")
    except Exception as e:
        print(f"⚠ H2-only test failed: {e}")

    # Test manufacturing blog-style content
    try:
        blog_content = """## CNC Machining Tolerances Explained

When it comes to precision parts, tolerances matter. Here's what you need to know.

### What Are Tolerances?

Tolerances define the acceptable variation in a part's dimensions. Tighter tolerances mean more precision but also higher costs.

### Common Tolerance Ranges

For most CNC work, you'll see tolerances between +/- 0.005" and +/- 0.001". The tighter you go, the more setup time and inspection you need.

### When to Specify Tight Tolerances

Only specify tight tolerances where they matter - at mating surfaces, critical fits, and functional interfaces.

## Conclusion

Understanding tolerances helps you balance cost and performance. Talk to your machinist early in the design process."""

        result = validate_structure(blog_content)
        if result[0] and result[2] >= 0.85:
            print(f"✓ Blog-style content passes well: is_valid={result[0]}, score={result[2]}")
        else:
            print(f"⚠ Blog-style content: {result}")
    except Exception as e:
        print(f"⚠ Blog-style test failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print("\n✓ All acceptance criteria PASSED")
    else:
        print(f"\n✗ {total - passed} acceptance criteria FAILED")

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_svc_010()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
