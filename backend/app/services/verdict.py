"""Verdict: a single, deterministic Recommended / Consider / Avoid call plus
a plain-English paragraph, built entirely from numbers the report has
already computed (score, deal label, confidence, red flags, known issues).
No new judgment is invented here - this is just the rule that turns those
existing signals into one clear recommendation.
"""

RECOMMENDED = "Recommended"
CONSIDER = "Consider"
AVOID = "Avoid"

GOOD_DEAL_LABELS = {"Exceptional Buy", "Good Buy"}
BAD_DEAL_LABELS = {"Overpriced", "Avoid"}


REPAIR_COST_EROSION_THRESHOLD = 0.25  # repair costs eating this share of market value bias the call down


def build_verdict(listing, score, deal_label, confidence, known_issues, red_flags, market_value=None, repair_estimate=None):
    severe_overdue = [i for i in known_issues if i["status"] == "overdue" and i["severity"] == "severe"]

    heavy_repair_burden = (
        repair_estimate is not None
        and market_value
        and repair_estimate["total_estimated_repair_cost_max"] >= market_value * REPAIR_COST_EROSION_THRESHOLD
    )

    if listing.title_status == "salvage" or severe_overdue:
        recommendation = AVOID
    elif confidence["level"] == "low" or deal_label in BAD_DEAL_LABELS:
        recommendation = CONSIDER
    elif heavy_repair_burden:
        # Repair costs alone eat a large share of the vehicle's value - even
        # a good on-paper deal shouldn't read as an unqualified Recommended.
        recommendation = CONSIDER
    elif deal_label in GOOD_DEAL_LABELS and confidence["level"] != "low":
        recommendation = RECOMMENDED
    else:
        recommendation = CONSIDER

    make = listing.generation.model.make.name
    model = listing.generation.model.name

    sentences = [
        f"This {listing.year} {make} {model} scores {score}/100 ({deal_label}), "
        f"with {confidence['level']} confidence in this assessment ({confidence['score']}/100)."
    ]

    if severe_overdue:
        titles = ", ".join(i["title"] for i in severe_overdue)
        sentences.append(f"It has severe known issue(s) past their typical onset mileage ({titles}), which drives this to an Avoid regardless of price.")
    elif listing.title_status == "salvage":
        sentences.append("Its salvage title alone is enough to recommend avoiding it without a full pre-purchase inspection.")
    elif red_flags:
        sentences.append(f"{len(red_flags)} red flag(s) were found - review them before deciding.")
    else:
        sentences.append("No red flags were found for this listing.")

    if heavy_repair_burden:
        sentences.append(
            f"The issues mentioned in the listing's description carry an estimated "
            f"${repair_estimate['total_estimated_repair_cost_min']:,.0f}-"
            f"${repair_estimate['total_estimated_repair_cost_max']:,.0f} in repair costs - "
            f"enough to erode a large share of this vehicle's value, which is why this isn't a straightforward Recommended."
        )

    if confidence["level"] == "low":
        sentences.append(
            "Confidence in this report is low - " + "; ".join(confidence["missing_data"]) + " would sharpen this assessment."
        )

    return {"recommendation": recommendation, "paragraph": " ".join(sentences)}
