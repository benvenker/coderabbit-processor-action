#!/usr/bin/env python3
"""Simple tests for coderabbit_processor.py.

Run with:

    python3 test_processor.py
"""

import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path so coderabbit_processor is importable
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from coderabbit_processor import (
    clean_comment_body,
    extract_severity,
    filter_outdated,
    infer_priority_fallback,
    resolve_thread_outdated,
)

tests_run = 0
tests_passed = 0


def test(name: str, condition: bool, error_msg: str = "") -> None:
    """Simple assertion helper that tracks results."""
    global tests_run, tests_passed
    tests_run += 1
    if condition:
        tests_passed += 1
        print(f"✓ {name}")
    else:
        print(f"✗ {name}")
        if error_msg:
            print(f"  {error_msg}")


def test_extract_severity_valid() -> None:
    """Test parsing CodeRabbit's severity format."""
    body = "_⚠️ Potential issue_ | _🟠 Major_\n\n**Fix this thing**"
    result = extract_severity(body)

    test("extract_severity: parses category", result["category"] == "Potential issue")
    test("extract_severity: parses severity", result["severity"] == "Major")
    test("extract_severity: maps to P1", result["priority"] == "P1")
    test("extract_severity: marks as parsed", result["parsed"] is True)


def test_extract_severity_fallback() -> None:
    """Test fallback when format not found."""
    body = "This is a comment with security vulnerability"
    result = extract_severity(body)

    test("extract_severity fallback: category unknown", result["category"] == "Unknown")
    test("extract_severity fallback: uses keyword P0", result["priority"] == "P0")
    test("extract_severity fallback: marks unparsed", result["parsed"] is False)


def test_extract_severity_edge_cases() -> None:
    """Test all known severities map correctly."""
    for severity, priority in [
        ("Critical", "P0"),
        ("Major", "P1"),
        ("Minor", "P2"),
        ("Trivial", "P3"),
    ]:
        body = f"_🧹 Nitpick_ | _🔵 {severity}_\n\nContent"
        result = extract_severity(body)
        test(
            f"extract_severity: {severity} -> {priority}",
            result["priority"] == priority and result["severity"] == severity,
        )


def test_filter_outdated_excludes() -> None:
    """Ensure outdated comments are removed when filtering is enabled."""
    threads = [
        {"comments": {"nodes": [{"outdated": False, "body": "Current"}]}},
        {"comments": {"nodes": [{"outdated": True, "body": "Outdated"}]}},
    ]

    filtered = filter_outdated(threads, exclude_outdated=True)
    test("filter_outdated: excludes outdated", len(filtered) == 1)
    if filtered:
        test(
            "filter_outdated: keeps current",
            filtered[0]["comments"]["nodes"][0]["body"] == "Current",
        )


def test_filter_outdated_includes() -> None:
    """Ensure outdated comments remain when filtering disabled."""
    threads = [
        {"comments": {"nodes": [{"outdated": False}]}},
        {"comments": {"nodes": [{"outdated": True}]}},
    ]

    filtered = filter_outdated(threads, exclude_outdated=False)
    test("filter_outdated: includes all when disabled", len(filtered) == 2)


def test_priority_fallback() -> None:
    """Test keyword-based priority inference."""
    test("priority P0: security keyword", infer_priority_fallback("This is a security issue") == "P0")
    test("priority P1: type safety keyword", infer_priority_fallback("Fix type safety here") == "P1")
    test("priority P2: style keyword", infer_priority_fallback("Refactor this code") == "P2")
    test("priority P3: default", infer_priority_fallback("Some random text here") == "P3")


def test_resolve_thread_outdated_variants() -> None:
    """Ensure outdated detection works for new and legacy data."""
    thread_outdated = {"isOutdated": True, "comments": {"nodes": [{"outdated": False}]}}
    comment_outdated = {"comments": {"nodes": [{"outdated": True}]}}
    legacy_comment = {"comments": {"nodes": [{"isOutdated": True}]}}
    current = {"comments": {"nodes": [{"outdated": False}]}}

    test("resolve_thread_outdated: prefers thread flag", resolve_thread_outdated(thread_outdated) is True)
    test("resolve_thread_outdated: uses comment outdated", resolve_thread_outdated(comment_outdated) is True)
    test("resolve_thread_outdated: supports legacy field", resolve_thread_outdated(legacy_comment) is True)
    test("resolve_thread_outdated: detects current thread", resolve_thread_outdated(current) is False)


def test_clean_comment() -> None:
    """Test HTML removal from comments."""
    body = "<!-- comment --><details>Detail</details>Test\n\n\n\nMore"
    cleaned = clean_comment_body(body)

    test("clean: removes HTML comments", "<!--" not in cleaned)
    test("clean: removes details tags", "<details>" not in cleaned and "</details>" not in cleaned)
    test("clean: collapses blank lines", "\n\n\n\n" not in cleaned)


def main() -> None:
    """Run all tests and report summary."""
    print("Running CodeRabbit Processor Tests\n")

    test_extract_severity_valid()
    test_extract_severity_fallback()
    test_extract_severity_edge_cases()
    test_filter_outdated_excludes()
    test_filter_outdated_includes()
    test_priority_fallback()
    test_resolve_thread_outdated_variants()
    test_clean_comment()

    print(f"\n{'=' * 50}")
    print(f"Tests: {tests_passed}/{tests_run} passed")

    if tests_passed == tests_run:
        print("✓ All tests passed!")
        sys.exit(0)

    print(f"✗ {tests_run - tests_passed} test(s) failed")
    sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
