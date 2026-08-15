# Analytical SQL

Seven hand-written, hand-verified queries against VehicleGrade's live schema, each answering a specific business question rather than demonstrating a syntax feature for its own sake. Every query in this folder was run against the actual seeded dev database (`instance/vehiclegrade.db`) before being committed — none of them are hypothetical.

Run any of them yourself:

```bash
cd backend
sqlite3 -header -column instance/vehiclegrade.db < sql/01_median_price_by_make_model.sql
```

(The schema is portable — no SQLite-only functions are used except `strftime()` for date truncation in query 2, which has a one-line equivalent in every other engine, e.g. Postgres `date_trunc('month', ...)`.)

| Query | Question it answers | Notable technique |
|---|---|---|
| [`01_median_price_by_make_model.sql`](01_median_price_by_make_model.sql) | What's the real median price per make/model, not just the average? | Median via `ROW_NUMBER()`/`COUNT() OVER (PARTITION BY ...)` — SQLite has no `MEDIAN()`/`PERCENTILE_CONT()`, so this is the portable window-function pattern used everywhere that's missing too |
| [`02_price_trend_by_month.sql`](02_price_trend_by_month.sql) | Is average price trending up or down month over month, per make? | `LAG() OVER (PARTITION BY make ORDER BY month)` for month-over-month % change, no self-join |
| [`03_days_on_market_by_title_status.sql`](03_days_on_market_by_title_status.sql) | Do salvage/rebuilt-title vehicles sit unsold longer than clean-title ones? | Plain `GROUP BY` — included as the baseline case the window-function queries build on |
| [`04_depreciation_curve_by_mileage_band.sql`](04_depreciation_curve_by_mileage_band.sql) | What does the real price-vs-mileage depreciation curve look like for a given model? | `CASE`-based bucketing, deliberately kept identical to `MILEAGE_BANDS` in `app/models/market_aggregate.py` so an ad-hoc query and the Gold-layer table can never disagree on what "50-100k" means |
| [`05_ingestion_funnel_by_source_type.sql`](05_ingestion_funnel_by_source_type.sql) | Which ingestion channel (paste vs. CSV) converts Bronze rows into Gold listings most reliably? | Multi-stage funnel via `LEFT JOIN` + `COUNT(DISTINCT CASE WHEN ...)`, verified against a real batch history (paste: 2/2 approved; CSV: 0/2, rolled back) |
| [`06_costliest_known_issues_by_generation.sql`](06_costliest_known_issues_by_generation.sql) | Which generations carry the most expensive severe known-issue exposure, and how many listings right now are actually past the onset mileage? | Reference-data table cross-referenced against live market rows to turn a static fact ("this issue exists") into a live count ("N cars today are at risk") |
| [`07_market_data_coverage_and_quality.sql`](07_market_data_coverage_and_quality.sql) | How much of the knowledge base has usable, confident market data behind it? | `LEFT JOIN` from the dimension (`generations`), not the fact table (`market_aggregates`) — a coverage report that only joined the other direction would silently hide the exact gaps it exists to surface |

## Why these live outside the ORM

Every one of these could be expressed through SQLAlchemy, and several already are in some form inside `app/services/` (e.g. `market_aggregation.py` computes something close to query 1, in Python, for the Gold-layer table). They're kept here as plain `.sql` files anyway because:

- They're meant to be read and run standalone — by a reviewer, in an interview, or from any BI tool that can point at the database — without needing the Flask app running or the ORM's model layer loaded.
- The median/funnel/coverage patterns here are reusable templates for questions the app doesn't have a dedicated service for yet, not one-off debugging queries.
