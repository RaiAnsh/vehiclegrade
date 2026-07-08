"""Seller Questions: generates situational questions a buyer should ask,
based on this specific listing's title status, mileage, known issues, and
how long it's been listed - not a generic checklist.
"""

from app.services.known_issues import evaluate_known_issues
from app.services.mileage_analysis import classify_mileage

TOP_ISSUE_QUESTIONS = 2
STALE_LISTING_DAYS = 21
HIGH_MILEAGE_RATIO_FOR_SERVICE_QUESTION = 1.2


def build_seller_questions(listing):
    questions = []

    mileage_ratio = classify_mileage(listing)["ratio"]

    if listing.title_status != "clean":
        questions.append("Can you share the title documentation? I'd like to confirm the exact title status.")

    if mileage_ratio > HIGH_MILEAGE_RATIO_FOR_SERVICE_QUESTION:
        questions.append("Has the transmission fluid and suspension been serviced given the mileage?")

    if not listing.description_text:
        questions.append("Do you have maintenance records or receipts available?")

    issues = evaluate_known_issues(listing)
    relevant_issues = [i for i in issues if i["status"] in ("common_now", "overdue")]
    relevant_issues.sort(key=lambda i: i["status"] == "overdue", reverse=True)
    for issue in relevant_issues[:TOP_ISSUE_QUESTIONS]:
        questions.append(f"Have you noticed any signs of {issue['title'].lower()}?")

    if listing.days_listed > STALE_LISTING_DAYS:
        questions.append("Is the price negotiable, given it's been listed a while?")

    if listing.location and listing.location.rust_belt_risk == "high":
        questions.append("Has the vehicle been rustproofed, and have you noticed any rust on the frame or rockers?")

    return questions
