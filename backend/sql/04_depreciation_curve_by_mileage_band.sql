-- Business question: "What does the real depreciation curve look like -
-- how much does average price actually drop per mileage band, for a given
-- model?" A scatter plot answers this visually; this is the same relationship
-- as a GROUP BY table, useful anywhere a chart isn't available (an export,
-- an email digest, a CLI report).
--
-- CASE-based bucketing here intentionally mirrors the fixed bands in
-- app/models/market_aggregate.py (MILEAGE_BANDS) rather than inventing a
-- second banding scheme - the Gold-layer table and this ad-hoc query should
-- always agree on what "50-100k" means.
--
-- Swap the make/model filter below for any other pair - this is a template
-- query, not a one-off.

SELECT
    CASE
        WHEN l.mileage_km < 50000  THEN '0-50k'
        WHEN l.mileage_km < 100000 THEN '50-100k'
        WHEN l.mileage_km < 150000 THEN '100-150k'
        WHEN l.mileage_km < 200000 THEN '150-200k'
        ELSE '200k+'
    END AS mileage_band,
    COUNT(*)                     AS sample_size,
    ROUND(AVG(l.price), 2)       AS avg_price,
    ROUND(AVG(l.mileage_km), 0)  AS avg_mileage_km
FROM listings l
JOIN generations g      ON g.id = l.generation_id
JOIN vehicle_models vmo ON vmo.id = g.model_id
JOIN vehicle_makes vm   ON vm.id = vmo.make_id
WHERE l.is_archived = 0
    AND vm.name = 'Honda'
    AND vmo.name = 'Civic'
GROUP BY mileage_band
ORDER BY avg_mileage_km;
