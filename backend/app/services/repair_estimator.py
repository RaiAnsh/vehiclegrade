"""Repair-cost estimator: reads a listing's own description text for
mentioned problems (broken transmission, cracked windshield, etc.) and turns
them into real repair-cost estimates.

Deterministic, keyword-based, and requires no LLM/API key - this is the tier
that must work today for every listing pasted from Facebook/Kijiji/AutoTrader.
An optional LLM-enhanced issue-detection tier can be layered on top of this
later without changing the shape of what this returns.

Matching is two-tier:
  1. Against the generation's own real KnownIssue rows first (title +
     symptoms) - if the description mentions something that matches a real
     documented issue for this exact generation, reuse its real cost range
     and tag it as reference_data, since that number isn't a guess.
  2. Against the generic common_repairs.json keyword list for anything the
     description mentions that isn't already covered by #1 - tagged as an
     estimate.

The LLM never computes numbers; this module doesn't either, beyond simple
min/max aggregation of numbers already present in the knowledge base.
"""

import json
import re
from pathlib import Path

KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent / "utils" / "vehicle_knowledge_base"

_common_repairs_cache = None


def _load_common_repairs():
    global _common_repairs_cache
    if _common_repairs_cache is None:
        with open(KNOWLEDGE_BASE_DIR / "common_repairs.json") as f:
            _common_repairs_cache = json.load(f)["repairs"]
    return _common_repairs_cache


def _phrase_present(text, phrase):
    """True if every word in `phrase` appears in `text` as a whole word,
    regardless of order - "windshield is cracked" should still match the
    keyword phrase "cracked windshield"."""
    words = phrase.split()
    return all(re.search(r"\b" + re.escape(word) + r"\b", text) for word in words)


def _text_mentions_any(text, keywords):
    return any(_phrase_present(text, keyword) for keyword in keywords if keyword.strip())


def detect_issues_from_text(description_text, known_issues):
    """Detect mentioned problems in a listing's description text.

    known_issues: the generation's KnownIssue rows (SQLAlchemy objects), used
    so a mentioned issue that matches a real documented one reuses its real
    cost range instead of falling back to a generic estimate.

    Returns a list of dicts, each shaped like:
      {title, source, matched_known_issue, estimated_repair_cost_min,
       estimated_repair_cost_max, severity}
    """
    if not description_text:
        return []

    text = description_text.lower()
    detected = []
    covered_common_repair_ids = set()

    # Tier 1: match against this generation's real known issues.
    for issue in known_issues:
        haystack_parts = [issue.title.lower()]
        if issue.symptoms:
            haystack_parts.append(issue.symptoms.lower())
        # Split the issue's own title/symptoms into candidate phrases so a
        # description mentioning "transmission slipping" matches a known
        # issue titled "Transmission slipping under load".
        candidate_phrases = set()
        for part in haystack_parts:
            candidate_phrases.add(part)
            candidate_phrases.update(w for w in part.replace(",", " ").split() if len(w) > 4)

        if _text_mentions_any(text, candidate_phrases):
            detected.append({
                "title": issue.title,
                "source": "reference_data",
                "matched_known_issue": True,
                "estimated_repair_cost_min": issue.estimated_repair_cost_min,
                "estimated_repair_cost_max": issue.estimated_repair_cost_max,
                "severity": issue.severity,
            })

    # Tier 2: match against the generic common-repairs reference list for
    # anything not already covered above.
    for repair in _load_common_repairs():
        if _text_mentions_any(text, repair["keywords"]):
            # Skip if a known issue already covered essentially the same
            # ground (avoid double-counting e.g. "transmission slipping"
            # once as a real known issue and again as a generic estimate).
            already_covered = any(
                repair["id"] not in covered_common_repair_ids
                and repair["title"].split()[0].lower() in d["title"].lower()
                for d in detected
            )
            if already_covered:
                continue

            covered_common_repair_ids.add(repair["id"])
            detected.append({
                "title": repair["title"],
                "source": "estimate",
                "matched_known_issue": False,
                "estimated_repair_cost_min": repair["estimated_cost_min"],
                "estimated_repair_cost_max": repair["estimated_cost_max"],
                "severity": repair["severity"],
            })

    return detected


def build_repair_estimate(description_text, known_issues, suggested_offer):
    """Build the full repair_estimate report section, or None if the
    description doesn't mention any detectable issues (or has no text)."""
    issues = detect_issues_from_text(description_text, known_issues)
    if not issues:
        return None

    total_min = sum(i["estimated_repair_cost_min"] for i in issues)
    total_max = sum(i["estimated_repair_cost_max"] for i in issues)

    return {
        "detected_issues": issues,
        "total_estimated_repair_cost_min": round(total_min, 2),
        "total_estimated_repair_cost_max": round(total_max, 2),
        "adjusted_offer_min": round(suggested_offer - total_max, 2),
        "adjusted_offer_max": round(suggested_offer - total_min, 2),
    }
