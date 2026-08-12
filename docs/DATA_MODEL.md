# VehicleGrade — Data Model & Architecture

This document is the entity-relationship reference for VehicleGrade's schema (19 tables, SQLAlchemy/SQLite, Postgres-compatible). It's organized around the same four layers the codebase itself is organized around — Reference Data, Market Data, Pipeline (Bronze/Silver/Gold), and Admin/Auth — because that split is the actual design decision the rest of the schema follows from, not just a documentation convenience.

For the formulas each engine runs on top of this data (Market Value, Known Issues, VehicleGrade Score, Confidence), see the [How It Works](../README.md#how-it-works) section of the main README — this document covers *what the data is*, not *what's computed from it*.

---

## 1. System architecture

```mermaid
flowchart TB
    subgraph Reference["Reference Data Layer — objective, price-independent"]
        direction LR
        RM[VehicleMake] --> RMo[VehicleModel] --> RG[Generation] --> RT[Trim]
        RG --> RE_link[GenerationEngine] --> RE[Engine]
        RG --> RKI[KnownIssue]
        RG --> RMa[MaintenanceItem]
    end

    subgraph Pipeline["Data Pipeline — Bronze -> Silver -> Gold (medallion)"]
        direction LR
        Bronze["Bronze\nRawListingSubmission\nImportBatch\n(immutable, as-submitted)"]
        Silver["Silver\nListingObservation\n(validated, deduped,\nquality-scored, reviewable)"]
        GoldL["Gold\nListing\n(materialized only on\nadmin approval)"]
        Bronze -->|"normalize + validate\n+ dedup + score"| Silver
        Silver -->|"admin approve\n(app/routes/admin_review.py)"| GoldL
    end

    subgraph MarketData["Market Data Layer"]
        direction LR
        Loc[Location]
        GoldL -.->|generation_id, location_id| Loc
        MA["MarketAggregate (Gold analytics)\nmedian/avg/p25/p75, by\nregion x title_status x mileage_band"]
        GoldL -->|"recompute_generation()\non every approve/rollback"| MA
    end

    subgraph Admin["Admin / Auth / Audit"]
        direction LR
        AU[AdminUser] --> RTk[RefreshToken]
        AU --> AAL[AdminAuditLog]
    end

    subgraph Intelligence["Intelligence Layer — APIs consume Reference + Gold, never raw Bronze"]
        direction LR
        MVE["Market Value Engine\n(reference data only)"]
        MCE["Comparable Engine\n(live Listing query)"]
        CE["Confidence Engine"]
        DE["Deal / Recommendation Engine"]
    end

    Reference --> Intelligence
    GoldL --> MCE
    MA --> Intelligence
    Pipeline -.->|every mutation logged| AAL
```

**Why this shape:** the Reference layer never looks at a price, mileage reading, or seller — it's the same fact set whether the cheapest or most expensive example of a vehicle is being evaluated. The Pipeline layer is the only path by which *observed* market data (pasted listings, CSV imports) can ever influence a user-facing number, and every promotion between its three stages is either fully automatic-and-deterministic (Bronze→Silver) or requires an explicit human decision (Silver→Gold). The Intelligence layer is a pure consumer of the first two — it has no ability to write to either.

---

## 2. Reference Data Layer

Objective vehicle knowledge. Never reads price, mileage, or listing data.

```mermaid
erDiagram
    VehicleMake ||--o{ VehicleModel : "has"
    VehicleModel ||--o{ Generation : "has"
    Generation ||--o{ Trim : "has"
    Generation ||--o{ KnownIssue : "has"
    Generation ||--o{ MaintenanceItem : "has"
    Generation ||--o{ GenerationEngine : "offered with"
    Engine ||--o{ GenerationEngine : "offered in"
    Engine ||--o{ Trim : "engine_id (optional)"
    Engine ||--o{ KnownIssue : "engine_id (optional)"
    Engine ||--o{ MaintenanceItem : "engine_id (optional)"

    VehicleMake {
        int id PK
        string name UK "Honda, Toyota, ..."
    }
    VehicleModel {
        int id PK
        int make_id FK
        string name "Civic"
    }
    Generation {
        int id PK
        int model_id FK
        string label "10th Gen"
        int start_year
        int end_year
        string body_type "sedan|suv|truck|hatchback"
        string drivetrain "FWD|AWD|RWD|4WD"
        int base_horsepower
        float fuel_economy_l_per_100km
        float reliability_stars "1.0-5.0"
        int typical_lifespan_km
        string parts_availability "excellent|good|fair|poor"
        string insurance_category "low|medium|high"
        float expected_annual_maintenance_cost
        string common_competitors "comma-separated, display only"
        float base_value "anchors Market Value Engine"
        int reference_mileage_km "base_value's reference point"
        datetime reference_reviewed_at "nullable, source freshness"
    }
    Trim {
        int id PK
        int generation_id FK
        int engine_id FK "nullable"
        string name "EX"
        float msrp_adjustment_pct "-0.06 .. +0.15"
        string engine_options "display string"
        string transmission_options "display string"
    }
    Engine {
        int id PK
        string name UK "EA888 Gen 3 2.0T"
        text description
        string manufacturer "nullable"
        string code "nullable, e.g. N20"
        float displacement_l "nullable"
        int cylinders "nullable"
        string configuration "nullable, I4|V6|..."
        string aspiration "nullable"
        string fuel_type "nullable"
        int production_start_year "nullable"
        int production_end_year "nullable"
        string source_name "provenance"
        string source_url "provenance"
        datetime reviewed_at "provenance"
        string confidence "verified|probable"
    }
    GenerationEngine {
        int id PK
        int generation_id FK
        int engine_id FK
        "UNIQUE(generation_id, engine_id)"
    }
    KnownIssue {
        int id PK
        int generation_id FK
        int engine_id FK "nullable, enables cross-generation matching"
        string title "AC compressor failure"
        text description
        string severity "minor|moderate|severe"
        int typical_mileage_km "onset mileage"
        float estimated_repair_cost_min
        float estimated_repair_cost_max
        text symptoms "nullable"
        text recommendation
    }
    MaintenanceItem {
        int id PK
        int generation_id FK
        int engine_id FK "nullable"
        string name "Transmission fluid"
        int interval_km
        float estimated_cost_min "nullable"
        float estimated_cost_max "nullable"
    }
```

**Provenance pattern:** `Engine` is the one reference table with explicit `source_name` / `source_url` / `reviewed_at` / `confidence` columns — deliberately, since engine identification is the fact most likely to be wrong if guessed, and the one other tables' `engine_id` links depend on being trustworthy. `Generation.reference_reviewed_at` exists for the same reason but isn't backfilled on every row yet (an honest, tracked gap, not a hidden one).

**Why `Engine` is separate from `Trim`:** the same engine family (e.g. Honda's L15B7) ships across multiple unrelated generations and models. Without `Engine`/`GenerationEngine` as their own tables, a known issue caused by an engine defect could only ever be entered once per generation, duplicated by hand everywhere else that engine appears — and silently miss any generation someone forgot to duplicate it into.

---

## 3. Market Data & Gold Analytics Layer

```mermaid
erDiagram
    Location ||--o{ Listing : "listed in"
    Generation ||--o{ Listing : "is a"
    Trim ||--o{ Listing : "trim of"
    Engine ||--o{ Listing : "engine_id (optional)"
    Generation ||--o{ MarketAggregate : "summarized by"

    Location {
        int id PK
        string city
        string region "ON, MB, AB, ... - MarketAggregate's region dimension"
        string rust_belt_risk "low|medium|high"
    }
    Listing {
        int id PK
        int generation_id FK
        int trim_id FK "nullable"
        int location_id FK
        int engine_id FK "nullable"
        int year
        int mileage_km
        float price
        string vin "nullable, display only - never used for scoring"
        string transmission
        string fuel_type
        string title_status "clean|rebuilt|salvage|unknown"
        string condition "excellent|good|fair|poor"
        float seller_rating
        int days_listed
        text description_text "nullable, source paste"
        string image_url "nullable, cosmetic only"
        string source "mock|admin_ingested"
        string external_url "nullable"
        datetime first_seen_at
        datetime last_seen_at
        bool is_archived "excluded from comparables + aggregates"
        datetime created_at
    }
    MarketAggregate {
        int id PK
        int generation_id FK
        string region "ALL sentinel for rollup"
        string title_status "ALL sentinel for rollup"
        string mileage_band "ALL sentinel; 0-50k .. 200k+"
        int sample_size
        float min_price
        float max_price
        float avg_price
        float median_price
        float price_p25
        float price_p75
        float price_stddev "null when sample_size < 2"
        int avg_mileage_km
        string market_confidence "low|medium|high"
        json sample_listing_ids "data lineage, capped at 50"
        datetime computed_at
        "UNIQUE(generation_id, region, title_status, mileage_band)"
    }
```

**`Listing` is the single Gold-layer fact table** two independent engines read from without ever writing to it directly:
- `market_comparables.py` queries it live, per request, for "what's similar asking right now."
- `market_aggregation.py` (`app/services/market_aggregation.py`) precomputes `MarketAggregate` from it — one row per generation × {region, title_status, mileage_band} slice actually present in the data, plus a grand-total rollup — recomputed automatically inside the same transaction as every admin approval or rollback.

**Why `region`/`title_status`/`mileage_band` use the string `"ALL"` instead of `NULL`:** SQLite (and several other engines) treat every `NULL` as distinct for uniqueness purposes, so a `UNIQUE(generation_id, region, title_status, mileage_band)` constraint couldn't actually prevent duplicate rollup rows if those columns were nullable. A named sentinel member is also the standard way an OLAP "ALL" rollup dimension is modeled, not a workaround unique to this schema.

**`is_archived`** is the one flag both live comparables and precomputed aggregates respect identically — a listing marked sold/removed (or archived by an admin rollback) disappears from both without a hard delete, since it may already be embedded in a historical report.

---

## 4. Pipeline (Bronze → Silver → Gold) & Admin/Auth Layer

```mermaid
erDiagram
    ImportBatch ||--o{ RawListingSubmission : "contains"
    RawListingSubmission ||--o| ListingObservation : "normalizes to"
    ListingObservation }o--|| Generation : "resolved to (nullable until matched)"
    ListingObservation }o--o| ListingObservation : "duplicate_of_observation_id"
    ListingObservation |o--o| Listing : "approved_listing_id (Silver -> Gold)"
    AdminUser ||--o{ ImportBatch : "created_by"
    AdminUser ||--o{ ListingObservation : "reviewed_by"
    AdminUser ||--o{ RefreshToken : "issued to"
    AdminUser ||--o{ AdminAuditLog : "acted as"

    ImportBatch {
        int id PK
        string source_type "paste_single|paste_multi|csv_upload"
        string status "open|processing|completed|rolled_back"
        string original_filename "nullable, CSV only"
        json column_mapping "nullable, CSV header -> canonical field"
        int created_by_id FK
        datetime created_at
        datetime processed_at "nullable"
        int row_count
        text notes "nullable"
    }
    RawListingSubmission {
        int id PK
        int import_batch_id FK
        int sequence_in_batch
        text raw_text "nullable, pasted block"
        json raw_row "nullable, verbatim CSV row"
        datetime submitted_at
    }
    ListingObservation {
        int id PK
        int import_batch_id FK
        int raw_submission_id FK "UNIQUE"
        int generation_id FK "nullable until resolved"
        int trim_id FK "nullable"
        int engine_id FK "nullable"
        int location_id FK "nullable"
        string make_raw "nullable, as parsed"
        string model_raw "nullable, as parsed"
        int year "nullable"
        int mileage_km "nullable"
        float price "nullable"
        string title_status "nullable"
        string condition "nullable"
        string transmission "nullable"
        string fuel_type "nullable"
        string source_identifier "nullable, opaque source ID"
        string external_url "nullable"
        string url_hash "nullable, sha256"
        string review_status "pending|needs_review|approved|rejected"
        int quality_score "0-100, nullable"
        json quality_factors "nullable, explainable deductions"
        int duplicate_of_observation_id FK "nullable, self-referential"
        json validation_errors "nullable, hard problems"
        json unresolved_fields "nullable, soft gaps"
        int reviewed_by_id FK "nullable"
        datetime reviewed_at "nullable"
        text rejection_reason "nullable"
        int approved_listing_id FK "nullable, Silver -> Gold link"
        datetime created_at
    }
    AdminUser {
        int id PK
        string email UK
        string password_hash
        string role "admin|reviewer|analyst"
        bool is_active
        datetime created_at
        datetime last_login_at "nullable"
    }
    RefreshToken {
        int id PK
        int user_id FK
        string token_hash UK "sha256, never the raw token"
        string csrf_token_hash
        datetime issued_at
        datetime expires_at
        datetime revoked_at "nullable"
        int replaced_by_id FK "nullable, self-referential rotation chain"
        string ip_address "nullable"
        string user_agent "nullable"
    }
    AdminAuditLog {
        int id PK
        int actor_id FK "nullable, e.g. failed login"
        string actor_email "nullable, denormalized"
        string action "e.g. observation.approve"
        string target_type "nullable"
        int target_id "nullable"
        json previous_values "nullable"
        json affected_record_ids "nullable"
        string ip_address "nullable"
        string user_agent "nullable"
        datetime created_at
    }
```

**The state machine that makes "unreviewed data can never become a market estimate" an enforced invariant, not a convention:** `ListingObservation.review_status` may only be changed by `app/routes/admin_review.py`, and `approved_listing_id` is the *only* path by which a `Listing` row is ever created from ingested data. Approval is hard-blocked by any remaining `unresolved_fields`/`validation_errors`, and by an unacknowledged `duplicate_of_observation_id` (an explicit `override_duplicate: true` is required to proceed anyway).

**Dedup is three signals in priority order:** exact `source_identifier` match → exact `url_hash` match (SHA-256 of a normalized URL, extracted by regex from pasted text or supplied directly for CSV rows) → same-generation + same-year + price within ±3% + mileage within ±1500 km. It only ever *flags* via `duplicate_of_observation_id` — a human makes the final call, nothing is auto-merged or auto-discarded.

**Auth is fully separate from the ingestion state machine on purpose:** `AdminUser.role` → `ROLE_PERMISSIONS` (`admin`: all; `reviewer`: ingest/review/view; `analyst`: view-only) is checked by a single `@require_permission(...)` decorator on every mutating route, so a role's actual capabilities live in exactly one place. `RefreshToken` stores only a SHA-256 hash of the token (never the raw value) with rotation-on-use (`replaced_by_id`) so a stolen refresh token, once reused, can have its whole chain revoked.

---

## Table index

| Table | Layer | Row created by |
|---|---|---|
| `vehicle_makes`, `vehicle_models`, `generations`, `trims`, `engines`, `generation_engines`, `known_issues`, `maintenance_items` | Reference | `flask seed-db` / `flask import-reference-data` / `flask import-engine-data` |
| `locations`, `listings` | Market Data | `flask seed-db` (mock) or `app/routes/admin_review.py` approval (real) |
| `market_aggregates` | Gold Analytics | `app/services/market_aggregation.py`, on every approval/rollback + `flask seed-db` |
| `import_batches`, `raw_listing_submissions`, `listing_observations` | Pipeline (Bronze/Silver) | `app/routes/admin_ingestion.py` |
| `admin_users`, `refresh_tokens`, `admin_audit_logs` | Admin/Auth | `flask create-admin-user`, `app/routes/auth.py`, `app/services/audit_log.py` |
| `feedback`, `community_comparables` | Standalone (not yet part of the medallion pipeline — see README Future Roadmap) | `app/routes/feedback.py`, `app/routes/community.py` |
