"""Regression snapshot guarding the known-issue/engine data model refactor.

Captures the load-bearing, easy-to-silently-break fields of `listing_detail()`
for a fixed set of seeded listings - score, verdict, confidence, and known
issue counts - so the upcoming Engine/GenerationEngine model change (and any
future refactor of the scoring/known-issue pipeline) can be checked against a
known-good baseline instead of relying on manual spot-checks.
"""

import json
from pathlib import Path

from app.extensions import db
from app.models import Listing
from app.services.serializers import listing_detail

SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "listing_detail_snapshot.json"
SAMPLE_LISTING_IDS = list(range(1, 11))


def _count_by_status(known_issues):
    counts = {}
    for issue in known_issues:
        counts[issue["status"]] = counts.get(issue["status"], 0) + 1
    return counts


def _snapshot_fields(detail):
    return {
        "vehicle": f"{detail['year']} {detail['make']} {detail['model']}",
        "vehiclegrade_score": detail["vehiclegrade_score"],
        "deal_label": detail["deal_label"],
        "verdict": detail["verdict"],
        "confidence_score": detail["confidence"]["score"],
        "confidence_level": detail["confidence"]["level"],
        "match_type": detail["confidence"]["match_type"],
        "known_issues_count": len(detail["known_issues"]),
        "known_issues_by_status": _count_by_status(detail["known_issues"]),
    }


def test_listing_detail_matches_snapshot(app):
    with app.app_context():
        actual = {}
        for listing_id in SAMPLE_LISTING_IDS:
            listing = db.session.get(Listing, listing_id)
            assert listing is not None, f"expected seeded listing id={listing_id}"
            actual[str(listing_id)] = _snapshot_fields(listing_detail(listing))

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert actual == expected
