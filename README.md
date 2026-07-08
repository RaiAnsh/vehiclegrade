# VehicleGrade

**Vehicle intelligence for smarter used car buyers.** VehicleGrade answers the question every used-car buyer actually has — *"Should I buy this car?"* — by combining an objective market valuation, a mileage-aware known-issues report, a maintenance forecast, and a rule-based negotiation assistant into one report, for any listing you paste in or enter by hand.

---

## Overview

Used-vehicle marketplaces show you a price and a mileage number and leave you to do the rest: is this actually a fair price? Is 140,000 km high or low for this particular model? Is there a well-known engine problem that shows up right around this mileage? VehicleGrade is a full-stack web app — Flask REST API, SQLite database, Next.js frontend — that answers all of that in one report, instantly, for any Make/Model/Year/Trim in its knowledge base.

## Problem / Product Vision

The product is built around the same core idea that shaped every generation of VehicleGrade: **separate "what is this vehicle worth" from "is this listing a good deal."**

- The **knowledge base** (`VehicleMake` → `VehicleModel` → `Generation` → `Trim`) is pure, objective vehicle data — specs, reliability, known issues, maintenance schedule. It never looks at a price, a mileage reading, or a seller. It's the same data whether you're buying the cheapest one in the country or the most expensive.
- A **Listing** is what varies per ad — price, mileage, location, seller rating, days listed — and is *scored against* the knowledge base entry it matches.

Keeping these separate is what makes both the Market Value Engine and the Known Issues report trustworthy: a 2017 Civic's timing chain issue is the same fact whether you're looking at a 40,000 km example or a 250,000 km one — only the *status* ("not yet relevant" vs. "overdue") changes, because that status is computed from the listing's mileage against the knowledge base's `typical_mileage_km`, not hardcoded per listing.

## Features

- **Full vehicle intelligence report**, for any listing: VehicleGrade Score (0–100, star rating, deal band), Market Value / Suggested Offer / Potential Savings, Vehicle Summary (engine, drivetrain, fuel economy, competitors), Reliability (stars, maintenance cost, lifespan, parts availability, insurance category), **mileage-aware Known Issues**, a 3-tier Maintenance Timeline (Immediate / Soon / Future), situational Seller Questions, a rule-based Negotiation Assistant (suggested offer + copyable message), Red Flags, and Ownership Cost (fuel + insurance + maintenance, annualized)
- **Two ways in**: a cascading Make → Model → Year → Trim manual form, or paste a free-text listing description and let a heuristic (regex-based, zero ML) parser prefill the form for you to review
- **Dashboard** — stat cards, a full filter panel (make/model, budget, mileage, year range, title status, transmission, fuel type, location), and a responsive grid of listing cards
- **Analytics** — average price by make/model, mileage vs. price scatter, vehicle distribution by body type, VehicleGrade Score distribution, and today's top deals
- **Generated vehicle glyphs** — every listing gets an inline SVG silhouette keyed by body type and title status; no stock photos, no external image dependencies

## Architecture

```
┌─────────────────┐        REST (JSON)        ┌──────────────────┐        ┌──────────────┐
│   Next.js App    │  ─────────────────────►  │   Flask API       │  ───►  │   SQLite      │
│  (React + TS)     │  ◄─────────────────────  │ (blueprints +     │  ◄───  │ (8 tables)    │
│  localhost:3000   │                           │  service layer)   │        │               │
└─────────────────┘                           └──────────────────┘        └──────────────┘
```

The frontend never computes a score, market value, or known-issue status itself — it only renders what the API returns. All of that logic lives once in `backend/app/services/`, so a Civic's known issues are computed identically whether they're rendered on the dashboard, the listing detail page, or the analyze page's result panel.

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend framework | Next.js 16 (App Router) + TypeScript | File-based routing, React Server/Client Components, strong typing end-to-end |
| Styling | Tailwind CSS v4 | Fast iteration, CSS-variable-based theming for the dark glassmorphism look |
| Animation | Framer Motion | Declarative entrance/hover animations without hand-rolled CSS keyframes |
| Charts | Recharts | Composable charting, including a scatter plot for mileage vs. price |
| Backend framework | Flask 3 (application factory + blueprints) | Lightweight, explicit, resume-recognizable pattern for structuring a non-trivial API |
| ORM / DB | Flask-SQLAlchemy + SQLite | An 8-table relational schema (knowledge base + listings) without hosted-DB overhead for a portfolio project |
| Cross-origin | Flask-Cors | Enables the Next.js dev server (3000) to call the Flask API (5001) |

## Project Structure

```
flipIQ/
  backend/
    run.py                       # entry point
    requirements.txt
    app/
      config.py                  # Config class (DB URI, etc.)
      extensions.py               # shared db = SQLAlchemy() instance
      models/                     # VehicleMake, VehicleModel, Generation, Trim,
                                   # KnownIssue, MaintenanceItem, Location, Listing
      services/
        market_value.py           # Market Value Engine
        known_issues.py            # mileage-aware known-issue status classification
        maintenance_timeline.py     # Immediate/Soon/Future service forecast
        ownership_cost.py           # fuel + insurance + maintenance, annualized
        deal_engine.py               # VehicleGrade Score, deal band, suggested offer
        red_flags.py, seller_questions.py, negotiation.py   # rule-based, situational text
        listing_parser.py            # free-text -> structured fields (regex/heuristic)
        stats_service.py             # aggregate queries for /stats
        serializers.py                # listing_summary() / listing_detail() dict builders
      routes/                      # catalog.py, listings.py, search.py, analyze.py,
                                    # parse_listing.py, stats.py
      utils/
        vehicle_knowledge_base/     # one JSON file per make - the knowledge base IS data
        seed_data.py                 # deterministic mock listing generator
        cli.py                        # `flask seed-db` command
  frontend/
    src/
      app/                        # landing, dashboard, analytics, analyze, listing/[id] pages
      components/
        dashboard/                 # VehicleGlyph, StarRating, ScoreBadge, ListingCard/Grid, FilterPanel
        report/                     # the 10-section vehicle intelligence report, shared by
                                     # listing/[id] and the analyze page's result panel
        analytics/                   # ChartCard + 6 chart/list components
        analyze/                      # InputModeToggle, ManualForm, PasteTextForm
        landing/                       # Hero, FeatureHighlights, GradientBackground
        ui/                             # hand-rolled Card, Button, Input, Select, Skeleton, Badge
      lib/                          # api.ts (typed fetch wrapper), types.ts (shared response shapes)
      hooks/                        # useListings, useStats, useCatalog, useDebounce
  v1-cli/                          # original CLI prototype (see Project History)
  v2-phone/                        # phone-marketplace generation (see Project History)
```

## How It Works

### Market Value Engine (`backend/app/services/market_value.py`)

Starts from a generation's `base_value` (anchored at a `reference_mileage_km`, clean title, base trim) and applies three independent multipliers:

```
market_value = base_value
             × (1 + trim_adjustment)      # trim's msrp_adjustment_pct, e.g. base -6% ... performance +15%
             × (1 + mileage_adjustment)   # ±0.0004%/km away from reference, capped at -35%/+15%
             × (1 + title_adjustment)     # clean 0% · unknown -10% · rebuilt -20% · salvage -45%
```

Worked example: a 2017 BMW 3-Series with a $16,500 base value at a 60,000 km reference, 104,000 km actual mileage, clean title, base trim → mileage delta of -44,000 km caps near its floor → market value lands around $14,300. This never looks at asking price, which is what lets `/analyze` reuse it on listings that were never saved to the database.

### Known Issues (`backend/app/services/known_issues.py`)

Every `KnownIssue` in the knowledge base has a `typical_mileage_km` — the mileage it commonly starts appearing at. A listing's actual mileage is compared against it as a ratio:

```
ratio = listing.mileage_km / typical_mileage_km
< 0.6   → not_yet_relevant   "Unlikely yet — typically appears around {typical_mileage_km:,} km"
< 0.9   → approaching        "Worth watching for — commonly starts near {typical_mileage_km:,} km"
< 1.3   → common_now         "Common at this mileage — inspect before buying"
≥ 1.3   → overdue            "Past the typical onset mileage — budget for this repair"
```

The same issue (e.g. a BMW N20 timing chain guide failure) reads completely differently on a 40,000 km car versus a 250,000 km one, because the *status* — not the issue itself — is a function of the listing.

### VehicleGrade Score (`backend/app/services/deal_engine.py`)

Starts at a neutral 50 and adjusts based on six factors, each logged as a plain-English reason:

1. **Price vs. market value** (dominant, ±45 points)
2. **Title status** (−30 to +5)
3. **Overdue known issues** (0 to −15, weighted by severity)
4. **Mileage vs. expected mileage for age** (−10 to +8, at 15,000 km/year)
5. **Seller rating** (−12 to +6)
6. **Days listed** (0 to +6 — longer-listed implies more negotiating room)

The final score is clamped to 0–100 and mapped to a band: **90–100 Exceptional Buy · 75–89 Good Buy · 60–74 Fair Deal · 40–59 Overpriced · <40 Avoid.**

**Suggested offer** anchors between the asking price and market value (a small discount if already fair, a larger pull toward market value if overpriced). Unlike the phone version, there's no "estimated flip profit" — vehicles aren't flipped the same way a phone is — so the only value metric beyond the score is **Potential Savings** (`market_value - price`).

### Listing Parser (`backend/app/services/listing_parser.py`)

A free-text description is run through a short list of regexes — a 4-digit year, `$`+digits for price, digits followed by "km"/"kms" for mileage, make/model matched against the loaded catalog, a title-status phrase match, a city matched against seeded locations. It's explicitly heuristic, not ML, and every extraction rule is a one-line regex. The result is a best-effort partial object that prefills the manual form — it's never persisted or submitted on its own, and the user reviews/corrects it before analyzing.

## Installation

**Backend**

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p instance
flask --app run.py seed-db     # seeds 11 makes, 20 models, 22 generations, ~176 mock listings
python run.py                   # runs on http://localhost:5001
```

**Frontend**

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                     # runs on http://localhost:3000
```

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/catalog` | Nested makes → models → generations → trims, powers cascading dropdowns |
| `GET` | `/listings` | List + filter listings (`make`, `model`, `max_price`, `max_mileage`, `min_year`, `max_year`, `title_status`, `transmission`, `fuel_type`, `location`) |
| `GET` | `/listing/<id>` | Full vehicle intelligence report for one listing |
| `POST` | `/search` | Same filters as `/listings`, as a JSON body |
| `POST` | `/analyze` | Full report for an arbitrary, non-persisted listing built from manual-form fields |
| `POST` | `/parse-listing` | `{text}` → best-effort `{year, make, model, price, mileage_km, title_status, transmission, location}` for prefilling the form |
| `GET` | `/stats` | Aggregate stats for the analytics dashboard |

## Future Roadmap

*Not implemented — ideas for a v4:*

- Real scraper/listing ingestion (Kijiji Autos, AutoTrader, Facebook Marketplace) replacing mock data
- Price-history tracking per listing over time, once there's a real, repeated data source
- VIN decoding to auto-resolve generation/trim instead of relying on year + user selection
- Live LLM-assisted negotiation messages, layered on top of (not replacing) the rule-based baseline
- User accounts, saved searches, and price-drop alerts
- Expanding the knowledge base beyond ~20 popular models toward the "thousands of vehicles" the schema is already built to support

## Project History

VehicleGrade has gone through three generations. It started as a simple Python CLI (`v1-cli/`) that scored phone listings against a same-model average. V2 (`v2-phone/`) rebuilt that as a full Flask/SQLite/Next.js phone-marketplace analyzer, introducing the Market Value Engine / VehicleGrade Score split that separates objective worth from deal quality. This V3 is a full pivot of that same architecture onto a richer domain — used vehicles — adding a knowledge base of make/model/generation/trim data (specs, reliability, known issues, maintenance) that's completely independent of any specific listing, plus the mileage-aware Known Issues engine, maintenance forecasting, and negotiation assistant that a single "market value" number couldn't capture on its own. Both prior generations are preserved untouched as a reference for how the project evolved.

## Lessons Learned

- **The value/deal-quality split scales across domains.** The same architectural decision that made the phone version's score trustworthy — never let the valuation engine see the price — turned out to generalize cleanly to a much richer domain. The vehicle knowledge base just has more objective attributes (reliability, known issues, maintenance) than a phone does, but the boundary is identical.
- **Knowledge base as data, not code, is what makes "mileage-aware" possible without an explosion of `if` statements.** Known issues, their typical onset mileage, and their severity all live in JSON, seeded into rows. The status-classification logic (`not_yet_relevant`/`approaching`/`common_now`/`overdue`) is a single small function that runs against every issue for every listing — adding vehicle #21 never touches that function.
- **A schema built for "thousands of vehicles" costs almost nothing at 20 models.** Generation-level knowledge, trim-level adjustments, and per-generation known issues/maintenance items are all separate tables from day one, so scaling the knowledge base is purely a data-entry problem, not a migration.
