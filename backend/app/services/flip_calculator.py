"""Flip Calculator: estimated profit/loss of buying a used vehicle privately in
Ontario, holding it for N months, then selling it privately.

Pure arithmetic over the same knowledge-base specs as market_value.py and
ownership_cost.py - no database writes, no ML. Every number traces to a named
constant below, and `assumptions` in the result lists the ones the caller
should sanity-check (insurance especially: for a young driver in the GTA it
is usually the single largest holding cost and varies enormously per person).
"""

from types import SimpleNamespace

from app.services.market_value import estimate_market_value
from app.services.ownership_cost import FUEL_PRICE_PER_LITER

ONTARIO_RST_RATE = 0.13  # retail sales tax paid by the buyer at registration on private sales
# Ontario computes RST on the greater of price paid and the vehicle's book
# (wholesale) value. We don't have a book value, so approximate it as a share
# of our own market estimate - a conservative guard against a "too good to be
# true" low price being taxed as if it were real.
BOOK_VALUE_SHARE_OF_MARKET = 0.85

UVIP_FEE = 20  # Used Vehicle Information Package, paid by the buyer
TRANSFER_FEE = 32  # ownership transfer
HISTORY_REPORT = 45  # CARFAX-type report
PRE_PURCHASE_INSPECTION = 175
SAFETY_CERTIFICATE = 150  # seller supplies one to sell; buyer needs it to register
DETAIL_AND_PREP = 150
LISTING_AND_ADMIN = 40

# Assumed annual insurance for a 20-year-old male in Scarborough/GTA with a
# G licence of limited history. Real quotes vary widely, so this is exposed as
# an override and flagged in `assumptions`.
YOUNG_DRIVER_INSURANCE_ANNUAL = {"low": 4000, "medium": 5000, "high": 7000}
PREMIUM_FUEL_MAKES = {"BMW", "Audi", "Infiniti", "Mercedes-Benz", "Lexus", "Acura"}
PREMIUM_FUEL_SURCHARGE_PER_LITER = 0.15

DEFAULT_KM_PER_MONTH = 800
MONTHLY_DEPRECIATION = 0.006  # of market value, per month held (age effect not in market_value.py)
SALE_DISCOUNT_FROM_MARKET = 0.03  # private buyers negotiate; expect to land under book
SCENARIO_SALE_SWING = {"optimistic": 0.05, "expected": 0.0, "pessimistic": -0.08}

REPAIR_SEVERITY_PROBABILITY = {"severe": 0.30, "moderate": 0.20, "minor": 0.10}
DEFAULT_TARGET_NET = -500  # "break even or a slight loss"


def _market_value_at(generation, trim, mileage_km, title_status, condition):
    attrs = SimpleNamespace(
        generation=generation, trim=trim, mileage_km=mileage_km, title_status=title_status, condition=condition,
    )
    return estimate_market_value(attrs)[0]


def estimate_repair_reserve(generation, mileage_km, planned_hold_km):
    """Probability-weighted repair exposure from the generation's known issues
    that are due (or near due) within this hold. Returns (reserve, items)."""
    horizon = mileage_km + planned_hold_km + 15000
    items = []
    for issue in generation.known_issues:
        if issue.typical_mileage_km > horizon:
            continue
        probability = REPAIR_SEVERITY_PROBABILITY.get(issue.severity, 0.10)
        midpoint = (issue.estimated_repair_cost_min + issue.estimated_repair_cost_max) / 2
        expected_cost = round(probability * midpoint)
        if expected_cost > 0:
            items.append({
                "issue": issue.title, "severity": issue.severity, "probability": probability,
                "cost_range": [issue.estimated_repair_cost_min, issue.estimated_repair_cost_max],
                "expected_cost": expected_cost,
            })
    items.sort(key=lambda i: i["expected_cost"], reverse=True)
    return sum(i["expected_cost"] for i in items), items


def _buying_costs(purchase_price, market_value):
    tax_base = max(purchase_price, BOOK_VALUE_SHARE_OF_MARKET * market_value)
    tax = round(tax_base * ONTARIO_RST_RATE)
    return {
        "purchase_price": round(purchase_price),
        "ontario_rst": tax,
        "uvip_and_transfer": UVIP_FEE + TRANSFER_FEE,
        "history_report": HISTORY_REPORT,
        "pre_purchase_inspection": PRE_PURCHASE_INSPECTION,
    }


def _holding_costs(generation, make_name, months, km_per_month, insurance_annual):
    fuel_price = FUEL_PRICE_PER_LITER + (PREMIUM_FUEL_SURCHARGE_PER_LITER if make_name in PREMIUM_FUEL_MAKES else 0)
    fuel = km_per_month * months / 100 * generation.fuel_economy_l_per_100km * fuel_price
    insurance = insurance_annual / 12 * max(months, 1)  # can't insure for less than a month in practice
    maintenance = generation.expected_annual_maintenance_cost / 12 * months
    return {"insurance": round(insurance), "fuel": round(fuel), "routine_maintenance": round(maintenance)}


def calculate_flip(generation, trim, make_name, *, purchase_price, mileage_km, months_held, title_status="clean",
                   condition="good", km_per_month=DEFAULT_KM_PER_MONTH, expected_sale_price=None,
                   repair_budget=None, insurance_annual=None, target_net=DEFAULT_TARGET_NET):
    months_held = max(float(months_held), 0.25)
    hold_km = round(km_per_month * months_held)
    market_now = _market_value_at(generation, trim, mileage_km, title_status, condition)
    market_at_sale = _market_value_at(generation, trim, mileage_km + hold_km, title_status, condition)

    assumptions = []
    if expected_sale_price is None:
        base_sale = market_at_sale * (1 - MONTHLY_DEPRECIATION * months_held) * (1 - SALE_DISCOUNT_FROM_MARKET)
        assumptions.append(
            f"Sale price estimated at VehicleGrade's market value after {hold_km:,} km of use, minus "
            f"{MONTHLY_DEPRECIATION:.1%}/month depreciation and a {SALE_DISCOUNT_FROM_MARKET:.0%} private-sale haggle."
        )
    else:
        base_sale = float(expected_sale_price)

    if insurance_annual is None:
        insurance_annual = YOUNG_DRIVER_INSURANCE_ANNUAL.get(generation.insurance_category, 5000)
        assumptions.append(
            f"Insurance assumed ${insurance_annual:,}/yr (20-year-old male, Scarborough). Real quotes vary widely "
            "with licence history and the exact car - get quotes for this VIN before you buy."
        )

    reserve_items = []
    if repair_budget is None:
        repair_budget, reserve_items = estimate_repair_reserve(generation, mileage_km, hold_km)
        assumptions.append(
            "Repair reserve is probability-weighted from this generation's known issues "
            "(severe 30%, moderate 20%, minor 10% chance within the hold) - a single severe failure can "
            "cost far more than this average."
        )

    buying = _buying_costs(purchase_price, market_now)
    holding = _holding_costs(generation, make_name, months_held, km_per_month, insurance_annual)
    selling = {"safety_certificate": SAFETY_CERTIFICATE, "detail_and_prep": DETAIL_AND_PREP, "listing_and_admin": LISTING_AND_ADMIN}

    total_buying = sum(buying.values())
    total_holding = sum(holding.values())
    total_selling = sum(selling.values())
    total_cost = total_buying + total_holding + total_selling + repair_budget

    scenarios = {}
    for name, swing in SCENARIO_SALE_SWING.items():
        sale = round(base_sale * (1 + swing))
        scenarios[name] = {"sale_price": sale, "net": round(sale - total_cost)}

    expected_net = scenarios["expected"]["net"]
    break_even_sale = round(total_cost)

    # Highest purchase price that still reaches `target_net` at the expected
    # sale price; bisection because RST depends on the price.
    low, high = 0.0, float(base_sale) * 1.5
    for _ in range(40):
        mid = (low + high) / 2
        cost_at_mid = (
            sum(_buying_costs(mid, market_now).values()) + total_holding + total_selling + repair_budget
        )
        if base_sale - cost_at_mid >= target_net:
            low = mid
        else:
            high = mid
    max_purchase_price = round(low / 50) * 50

    if expected_net >= 0:
        verdict = "profitable"
    elif expected_net >= target_net:
        verdict = "break_even"
    elif scenarios["optimistic"]["net"] >= target_net:
        verdict = "only_works_if_sale_goes_well"
    else:
        verdict = "likely_loss"

    warnings = []
    if title_status in ("rebuilt", "salvage"):
        warnings.append("Rebuilt/salvage titles are slow to resell and many insurers won't cover them - treat the sale estimate as optimistic.")
    if purchase_price > max_purchase_price:
        warnings.append(f"At ${purchase_price:,.0f} this misses your target of {target_net:+,}; offer at most about ${max_purchase_price:,}.")
    if months_held < 1:
        warnings.append("Holds under a month still cost a full month of insurance in this estimate.")

    return {
        "market_value_now": round(market_now),
        "expected_hold_km": hold_km,
        "months_held": months_held,
        "costs": {
            "buying": buying, "holding": holding, "selling": selling,
            "repair_reserve": round(repair_budget),
            "totals": {
                "buying": round(total_buying), "holding": round(total_holding), "selling": round(total_selling),
                "all_in": round(total_cost),
            },
        },
        "repair_reserve_items": reserve_items,
        "scenarios": scenarios,
        "expected_net": expected_net,
        "monthly_cost_to_hold": round(total_holding / months_held),
        "break_even_sale_price": break_even_sale,
        "target_net": target_net,
        "max_purchase_price": max_purchase_price,
        "verdict": verdict,
        "warnings": warnings,
        "assumptions": assumptions,
    }
