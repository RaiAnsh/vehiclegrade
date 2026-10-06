"""Public flip tools: GET /flip/roadmap and the stateless POST /flip/ledger/summarize
(users' flips live in their browser; the server only does the arithmetic)."""

from app.services.flip_roadmap import level_for


def _predict(client, **overrides):
    body = {"make": "Honda", "model": "Accord", "year": 2010, "trim": "EX-L V6", "mileage_km": 175000,
            "purchase_price": 7000, "months_held": 3, **overrides}
    return client.post("/flip-calculator", json=body).get_json()


def _flip(flip_id, predicted, make="Honda", model="Accord", status="holding", **extra):
    flip = {"id": flip_id, "make": make, "model": model, "status": status, "purchase_date": "2026-01-01",
            "purchase_price": 7000, "purchase_tax": 910, "purchase_fees": 100, "predicted": predicted,
            "expenses": [{"category": "insurance", "amount": 1000}, {"category": "repair", "amount": 450},
                         {"category": "fuel", "amount": 300}]}
    flip.update(extra)
    return flip


def _sold(flip_id, predicted, sale_price, **kw):
    return _flip(flip_id, predicted, status="sold", sale_price=sale_price, sale_date="2026-04-01", sale_fees=150, **kw)


def test_roadmap_has_five_ordered_levels_and_every_car_is_in_the_catalog(client):
    levels = client.get("/flip/roadmap").get_json()["levels"]
    assert [l["level"] for l in levels] == [1, 2, 3, 4, 5]
    catalog = client.get("/catalog").get_json()
    known = {(m["name"].lower(), mo["name"].lower()) for m in catalog["makes"] for mo in m["models"]}
    for level in levels:
        for car in level["cars"]:
            assert (car["make"].lower(), car["model"].lower()) in known, car
    assert level_for("honda", "ACCORD") == 1
    assert level_for("BMW", "3-Series") == 5
    assert level_for("Ford", "F-150") is None


def test_summarize_matches_ledger_math_and_reports_progress(client):
    predicted = _predict(client)
    # 10000 - 150 - (7000+910+100) - 1750 = 90
    body = client.post("/flip/ledger/summarize", json={"flips": [_sold(1, predicted, 10000), _flip(2, predicted)]}).get_json()
    sold = body["flips"]["1"]
    assert sold["level"] == 1
    assert sold["summary"]["actual_net"] == 90.0
    assert sold["summary"]["comparison"]["net_error"] == 90 - predicted["expected_net"]
    holding = body["flips"]["2"]["summary"]
    assert holding["actual_net"] is None and holding["break_even_sale_price"] > holding["total_invested"]
    assert body["portfolio"]["flips_sold"] == 1 and body["portfolio"]["flips_holding"] == 1
    assert body["progress"]["current_level"] == 1  # only 1 sold, needs 2 to graduate
    assert body["progress"]["levels"][0]["graduated"] is False


def test_two_good_sales_graduate_a_level(client):
    predicted = _predict(client)
    flips = [_sold(1, predicted, 10000), _sold(2, predicted, 9800)]
    progress = client.post("/flip/ledger/summarize", json={"flips": flips}).get_json()["progress"]
    assert progress["levels"][0]["graduated"] is True
    assert progress["levels"][1]["unlocked"] is True
    assert progress["current_level"] == 2


def test_two_big_losses_do_not_graduate(client):
    predicted = _predict(client)
    flips = [_sold(1, predicted, 6000), _sold(2, predicted, 6000)]
    progress = client.post("/flip/ledger/summarize", json={"flips": flips}).get_json()["progress"]
    assert progress["levels"][0]["graduated"] is False
    assert progress["levels"][1]["unlocked"] is False


def test_malformed_prediction_is_ignored_not_crashing(client):
    body = client.post("/flip/ledger/summarize", json={"flips": [_sold(1, {"costs": "garbage"}, 10000)]})
    assert body.status_code == 200
    assert body.get_json()["flips"]["1"]["summary"]["comparison"] is None


def test_bad_input_rejected(client):
    assert client.post("/flip/ledger/summarize", json={}).status_code == 400
    assert client.post("/flip/ledger/summarize", json={"flips": [{"status": "weird"}]}).status_code == 400
    assert client.post("/flip/ledger/summarize", json={"flips": [_flip(1, None, purchase_price=-5)]}).status_code == 400
    assert client.post("/flip/ledger/summarize", json={"flips": [_flip(1, None, purchase_date="nope")]}).status_code == 400
    bad_expense = _flip(1, None)
    bad_expense["expenses"] = [{"category": "snacks", "amount": 5}]
    assert client.post("/flip/ledger/summarize", json={"flips": [bad_expense]}).status_code == 400
    assert client.post("/flip/ledger/summarize", json={"flips": [_flip(i, None) for i in range(101)]}).status_code == 400
    assert client.post("/flip/ledger/summarize", json={"flips": [_sold(1, None, 9000, purchase_date="2027-01-01")]}).status_code == 400
