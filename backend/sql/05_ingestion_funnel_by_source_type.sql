-- Business question: "Which ingestion channel (single paste, multi paste,
-- CSV upload) actually converts into usable market data most reliably?" -
-- the kind of funnel/conversion-rate report a data analyst is asked to
-- build for almost any pipeline with a human-review step.
--
-- Three-way LEFT JOIN Bronze -> Silver, aggregated by ImportBatch.source_type:
--   raw_submissions   = Bronze  (every row ever submitted)
--   observations      = Silver  (every row that got normalized/scored)
--   approved          = Gold    (every row that became a real Listing)
-- LEFT JOIN (not INNER) matters here - a raw_submission technically could
-- exist without an observation if a batch was created but never processed,
-- and this funnel should still count it as a Bronze row that never
-- converted, not silently exclude it.

SELECT
    ib.source_type,
    COUNT(DISTINCT rls.id)                                                  AS bronze_rows,
    COUNT(DISTINCT lo.id)                                                   AS silver_rows,
    COUNT(DISTINCT CASE WHEN lo.review_status = 'approved' THEN lo.id END)  AS gold_rows,
    COUNT(DISTINCT CASE WHEN lo.review_status = 'rejected' THEN lo.id END)  AS rejected_rows,
    COUNT(DISTINCT CASE WHEN lo.duplicate_of_observation_id IS NOT NULL THEN lo.id END) AS flagged_duplicate_rows,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN lo.review_status = 'approved' THEN lo.id END)
        / NULLIF(COUNT(DISTINCT rls.id), 0),
        1
    ) AS pct_bronze_to_gold
FROM import_batches ib
LEFT JOIN raw_listing_submissions rls ON rls.import_batch_id = ib.id
LEFT JOIN listing_observations lo     ON lo.raw_submission_id = rls.id
GROUP BY ib.source_type
ORDER BY pct_bronze_to_gold DESC;
