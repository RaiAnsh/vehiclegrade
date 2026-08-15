-- Business question: "Across the whole knowledge base, which generations
-- carry the most expensive known-issue exposure, and how much of that
-- exposure is actually 'live' for cars currently in the marketplace data
-- (i.e. sitting at or past the issue's typical onset mileage)?"
--
-- The "currently relevant" column is what makes this more than a static
-- reference dump - it cross-references the reference-data KnownIssue table
-- against real Listing rows to answer "how many cars out there right now
-- are actually at risk of this," the same mileage-ratio logic
-- app/services/known_issues.py applies to a single listing, aggregated
-- across the whole market sample instead.

SELECT
    vm.name || ' ' || vmo.name || ' (' || g.label || ')' AS generation,
    ki.title,
    ki.severity,
    ki.typical_mileage_km,
    ROUND((ki.estimated_repair_cost_min + ki.estimated_repair_cost_max) / 2.0, 2) AS avg_repair_cost,
    COUNT(DISTINCT CASE
        WHEN l.mileage_km >= ki.typical_mileage_km AND l.is_archived = 0 THEN l.id
    END) AS listings_currently_at_or_past_onset
FROM known_issues ki
JOIN generations g      ON g.id = ki.generation_id
JOIN vehicle_models vmo ON vmo.id = g.model_id
JOIN vehicle_makes vm   ON vm.id = vmo.make_id
LEFT JOIN listings l    ON l.generation_id = g.id
WHERE ki.severity = 'severe'
GROUP BY ki.id
ORDER BY avg_repair_cost DESC
LIMIT 15;
