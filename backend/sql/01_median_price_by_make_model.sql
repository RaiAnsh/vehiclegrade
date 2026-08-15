-- Business question: "What's the real median asking price for each
-- make/model, not just the average (which a handful of high-end trims can
-- skew)?"
--
-- SQLite has no MEDIAN()/PERCENTILE_CONT() aggregate, so this uses the
-- standard window-function median pattern: rank every row within its group
-- by price, then average the middle row (odd count) or middle two rows
-- (even count). ROW_NUMBER()/COUNT() OVER (PARTITION BY ...) is the same
-- windowing primitive every mainstream analytics warehouse (BigQuery,
-- Snowflake, Postgres, Fabric/Synapse) supports, so this pattern ports
-- directly - only the two window-function calls need porting, never the
-- surrounding logic.
--
-- Only non-archived listings count (archived = sold/removed, excluded from
-- every other market-facing calculation in this app too - see
-- app/services/market_comparables.py).

WITH ranked AS (
    SELECT
        vm.name AS make,
        vmo.name AS model,
        l.price,
        ROW_NUMBER() OVER (PARTITION BY vm.name, vmo.name ORDER BY l.price) AS row_num,
        COUNT(*)     OVER (PARTITION BY vm.name, vmo.name)                 AS row_count
    FROM listings l
    JOIN generations g      ON g.id = l.generation_id
    JOIN vehicle_models vmo ON vmo.id = g.model_id
    JOIN vehicle_makes vm   ON vm.id = vmo.make_id
    WHERE l.is_archived = 0
)
SELECT
    make,
    model,
    row_count                                  AS sample_size,
    ROUND(AVG(price), 2)                       AS median_price,   -- the AVG collapses to a single value: the middle row(s)
    MIN(price)                                 AS min_price,
    MAX(price)                                 AS max_price
FROM ranked
WHERE row_num IN ((row_count + 1) / 2, (row_count + 2) / 2)  -- middle row for odd counts, both middle rows for even counts
GROUP BY make, model
ORDER BY median_price DESC;
