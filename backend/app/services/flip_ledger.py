"""Pure functions turning a Flip row (+ its expenses) into the numbers the
ledger shows: running cost, actual profit/loss, and actual-vs-predicted.
"""

from datetime import date

from app.services.flip_calculator import DETAIL_AND_PREP, LISTING_AND_ADMIN, SAFETY_CERTIFICATE

DAYS_PER_MONTH = 30.44

# Calculator line -> ledger expense category it should be compared with.
PREDICTED_VS_ACTUAL_CATEGORIES = {
    "insurance": ("holding", "insurance"),
    "fuel": ("holding", "fuel"),
    "maintenance": ("holding", "routine_maintenance"),
}


def expenses_by_category(flip):
    totals = {}
    for expense in flip.expenses:
        totals[expense.category] = totals.get(expense.category, 0) + expense.amount
    return {category: round(amount, 2) for category, amount in totals.items()}


def months_elapsed(flip, today=None):
    end = flip.sale_date or today or date.today()
    return round(max((end - flip.purchase_date).days, 0) / DAYS_PER_MONTH, 2)


def summarize_flip(flip, today=None):
    by_category = expenses_by_category(flip)
    expenses_total = round(sum(by_category.values()), 2)
    acquisition = round(flip.purchase_price + flip.purchase_tax + flip.purchase_fees, 2)
    invested = round(acquisition + expenses_total, 2)
    months = months_elapsed(flip, today)

    summary = {
        "acquisition_cost": acquisition,
        "expenses_total": expenses_total,
        "expenses_by_category": by_category,
        "total_invested": invested,
        "months_held": months,
        "monthly_burn": round(expenses_total / months, 2) if months > 0 else None,
    }

    if flip.status == "sold" and flip.sale_price is not None:
        proceeds = round(flip.sale_price - flip.sale_fees, 2)
        summary["net_proceeds"] = proceeds
        summary["actual_net"] = round(proceeds - invested, 2)
    else:
        # Cheapest sale that still breaks even: money already in, plus the
        # typical selling costs (safety, detail, listing) not yet paid.
        selling_costs = SAFETY_CERTIFICATE + DETAIL_AND_PREP + LISTING_AND_ADMIN
        summary["break_even_sale_price"] = round(invested + selling_costs, 2)
        summary["actual_net"] = None

    summary["comparison"] = compare_to_prediction(flip, summary)
    return summary


def compare_to_prediction(flip, summary):
    """Actual-vs-predicted rows. Only meaningful once sold; for a flip that's
    still held, only cost lines are comparable (pro-rated by months so far)."""
    predicted = flip.predicted
    if not predicted:
        return None

    rows = []
    predicted_months = predicted["months_held"]
    actual_months = summary["months_held"]

    for label, (group, key) in PREDICTED_VS_ACTUAL_CATEGORIES.items():
        predicted_cost = predicted["costs"][group].get(key, 0)
        actual_cost = summary["expenses_by_category"].get(label, 0)
        if flip.status != "sold" and predicted_months:
            predicted_cost = predicted_cost * min(actual_months / predicted_months, 1)
        rows.append({"line": label, "predicted": round(predicted_cost), "actual": round(actual_cost)})

    rows.append({"line": "repairs", "predicted": round(predicted["costs"]["repair_reserve"]),
                 "actual": round(summary["expenses_by_category"].get("repair", 0))})

    comparison = {"lines": rows, "predicted_net": predicted["expected_net"], "predicted_months": predicted_months,
                  "predicted_sale_price": predicted["scenarios"]["expected"]["sale_price"]}

    if flip.status == "sold" and summary.get("actual_net") is not None:
        comparison["actual_net"] = summary["actual_net"]
        comparison["net_error"] = round(summary["actual_net"] - predicted["expected_net"])
        comparison["sale_price_error"] = round(flip.sale_price - comparison["predicted_sale_price"])
        comparison["months_error"] = round(actual_months - predicted_months, 2)
    return comparison


def portfolio_summary(flips):
    sold = [f for f in flips if f.status == "sold" and f.sale_price is not None]
    holding = [f for f in flips if f.status == "holding"]
    sold_summaries = [(f, summarize_flip(f)) for f in sold]

    nets = [s["actual_net"] for _, s in sold_summaries]
    wins = [n for n in nets if n >= 0]
    errors = [s["comparison"]["net_error"] for _, s in sold_summaries if s["comparison"] and "net_error" in s["comparison"]]

    return {
        "flips_total": len(flips),
        "flips_sold": len(sold),
        "flips_holding": len(holding),
        "total_net": round(sum(nets), 2) if nets else 0,
        "avg_net": round(sum(nets) / len(nets), 2) if nets else None,
        "win_rate_pct": round(len(wins) / len(nets) * 100, 1) if nets else None,
        "avg_months_held": round(sum(s["months_held"] for _, s in sold_summaries) / len(sold), 2) if sold else None,
        "capital_in_holding": round(sum(summarize_flip(f)["total_invested"] for f in holding), 2),
        "prediction": {
            "flips_compared": len(errors),
            "avg_net_error": round(sum(errors) / len(errors), 2) if errors else None,
            "note": "Positive error = the flip did better than the calculator predicted.",
        } if errors else None,
    }
