#!/usr/bin/env python3
"""Validate a constrained three-word English theme against image evidence."""

import argparse
import json
import re
from pathlib import Path


FILLER = {"a", "an", "the", "and", "with", "for", "of", "in", "on"}
BANNED = {
    "amazing", "beautiful", "perfect", "magical", "unforgettable",
    "lifestyle", "aesthetic", "vibes",
}


def terms(values):
    result = set()
    for value in values:
        text = value.get("term", "") if isinstance(value, dict) else value
        result.update(token.lower() for token in re.findall(r"[A-Za-z]+", text))
    return result


def support_count(mapping, word):
    value = mapping.get(word, mapping.get(word.title(), []))
    if isinstance(value, dict):
        images = value.get("images", [])
        return len(set(images)), bool(value.get("whole_set", False))
    return len(set(value)), False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()

    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    words = args.title.split()
    lower = [word.lower() for word in words]
    anchors = terms(evidence.get("anchors", []))
    contexts = terms(evidence.get("contexts", []) + evidence.get("moods", []))
    endings = terms(evidence.get("endings", []))
    unsupported = terms(evidence.get("unsupported", []))
    anchor_word = lower[0] if len(lower) == 3 else ""
    context_word = lower[1] if len(lower) == 3 else ""
    ending_word = lower[2] if len(lower) == 3 else ""
    anchor_count, anchor_whole = support_count(evidence.get("anchor_support", {}), anchor_word)
    context_count, context_whole = support_count(evidence.get("context_support", {}), context_word)

    checks = {
        "ascii_letters_and_spaces": bool(re.fullmatch(r"[A-Za-z ]+", args.title)),
        "title_case": args.title == args.title.title(),
        "exactly_three_words": len(words) == 3,
        "length_15_to_26": 15 <= len(args.title) <= 26,
        "no_repeated_words": len(set(lower)) == len(lower),
        "no_filler": not any(word in FILLER for word in lower),
        "no_banned_promotional_words": not any(word in BANNED for word in lower),
        "first_word_is_anchor": anchor_word in anchors,
        "anchor_supported_by_two_images": anchor_count >= 2 or anchor_whole,
        "second_word_is_context": context_word in contexts,
        "context_supported_by_two_images": context_count >= 2 or context_whole,
        "third_word_is_approved_ending": ending_word in endings,
        "contains_no_unsupported_term": not any(word in unsupported for word in lower),
    }
    report = {
        "title": args.title,
        "passed": all(checks.values()),
        "checks": checks,
        "anchor_support_count": anchor_count,
        "context_support_count": context_count,
        "context_whole_set": context_whole,
    }
    output = json.dumps(report, indent=2)
    if args.report:
        Path(args.report).write_text(output, encoding="utf-8")
    print(output)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
