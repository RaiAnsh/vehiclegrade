"""POST /flip-calculator: Ontario buy-hold-sell profit/loss estimate."""

BASE = {
    "make": "Honda", "model": "Accord", "year": 2010, "mileage_km": 180000,
    "purchase_price": 7000, "months_held": 3, "title_status": "clean", "condition": "good",
}


def _post(client, **overrides):
    return client.post("/flip-calculator", json={**BASE, **overrides})


def test_returns_itemised_costs_that_sum_to_all_in(client):
    body = _post(client).get_json()
    costs = body["costs"]
    parts = costs["totals"]["buying"] + costs["totals"]["holding"] + costs["totals"]["selling"] + costs["repair_reserve"]
    assert abs(parts - costs["totals"]["all_in"]) <= 2  # independent rounding of the line items
    assert costs["buying"]["ontario_rst"] >= round(0.13 * BASE["purchase_price"])
    assert body["break_even_sale_price"] == costs["totals"]["all_in"]


def test_scenarios_are_ordered_and_net_matches_sale_minus_cost(client):
    body = _post(client).get_json()
    s = body["scenarios"]
    assert s["pessimistic"]["net"] < s["expected"]["net"] < s["optimistic"]["net"]
    assert s["expected"]["net"] == s["expected"]["sale_price"] - body["costs"]["totals"]["all_in"]


def test_longer_hold_costs_more(client):
    short = _post(client, months_held=1).get_json()
    long = _post(client, months_held=6).get_json()
    assert long["costs"]["totals"]["holding"] > short["costs"]["totals"]["holding"]
    assert long["expected_net"] < short["expected_net"]


def test_buying_at_max_purchase_price_hits_target(client):
    first = _post(client).get_json()
    at_max = _post(client, purchase_price=first["max_purchase_price"], expected_sale_price=first["scenarios"]["expected"]["sale_price"]).get_json()
    assert at_max["expected_net"] >= first["target_net"] - 120  # max price is rounded to $50, RST included


def test_overrides_are_respected(client):
    body = _post(client, insurance_annual=1200, repair_budget=0, expected_sale_price=9000).get_json()
    assert body["costs"]["holding"]["insurance"] == 300  # 1200/12 * 3 months
    assert body["costs"]["repair_reserve"] == 0
    assert body["scenarios"]["expected"]["sale_price"] == 9000
    assert not any("Insurance assumed" in a for a in body["assumptions"])


def test_bad_input_is_rejected(client):
    assert client.post("/flip-calculator", json={"make": "Honda"}).status_code == 400
    assert _post(client, make="Nonexistent").status_code == 400
    assert _post(client, purchase_price="abc").status_code == 400
    assert _post(client, months_held=0).status_code == 400
    assert _post(client, year=1950).status_code == 400
