-- Business question: "How much of the knowledge base actually has usable
-- market data behind it, and how confident is it?" - a data-quality/
-- coverage report, the kind of thing a data analyst is asked for before
-- anyone trusts a metric built on top of a dataset.
--
-- LEFT JOIN from generations (not market_aggregates) is deliberate: a
-- generation with zero rows in market_aggregates still needs to appear in
-- this report, as a 'no data yet' row - counting only what exists in the
-- fact table would silently hide the actual coverage gap, which is the
-- entire point of a coverage report.

SELECT
    vm.name || ' ' || vmo.name || ' (' || g.label || ')' AS generation,
    COALESCE(ma.sample_size, 0)         AS market_sample_size,
    COALESCE(ma.market_confidence, 'no_data') AS market_confidence,
    ma.median_price,
    ma.computed_at
FROM generations g
JOIN vehicle_models vmo ON vmo.id = g.model_id
JOIN vehicle_makes vm   ON vm.id = vmo.make_id
LEFT JOIN market_aggregates ma
    ON ma.generation_id = g.id
    AND ma.region = 'ALL' AND ma.title_status = 'ALL' AND ma.mileage_band = 'ALL'  -- the grand-total rollup row only
ORDER BY
    CASE COALESCE(ma.market_confidence, 'no_data')
        WHEN 'no_data' THEN 0 WHEN 'low' THEN 1 WHEN 'medium' THEN 2 WHEN 'high' THEN 3
    END,
    generation;

-- Roll this up into a single coverage summary instead of a per-generation list:
--
-- SELECT
--     COALESCE(ma.market_confidence, 'no_data') AS market_confidence,
--     COUNT(*) AS generation_count,
--     ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM generations), 1) AS pct_of_catalog
-- FROM generations g
-- LEFT JOIN market_aggregates ma
--     ON ma.generation_id = g.id
--     AND ma.region = 'ALL' AND ma.title_status = 'ALL' AND ma.mileage_band = 'ALL'
-- GROUP BY market_confidence
-- ORDER BY generation_count DESC;
