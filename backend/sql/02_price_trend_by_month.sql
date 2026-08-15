-- Business question: "Is the average asking price for this make trending up
-- or down month over month?"
--
-- Uses first_seen_at (when a listing entered the dataset) as the time axis,
-- not created_at - first_seen_at is what already carries meaning for a real
-- scraper feed (see Listing model docstring: "lets duplicate postings be
-- recognized and sold/removed listings archived"), so this query keeps
-- working unchanged once mock listings are replaced by a real feed.
--
-- month-over-month % change uses LAG() - a single window function instead
-- of a self-join, and the pattern generalizes directly to any other
-- month-over-month metric in this schema (median price, sample size, etc.).

WITH monthly AS (
    SELECT
        vm.name AS make,
        strftime('%Y-%m', l.first_seen_at) AS month,
        COUNT(*) AS sample_size,
        ROUND(AVG(l.price), 2) AS avg_price
    FROM listings l
    JOIN generations g      ON g.id = l.generation_id
    JOIN vehicle_models vmo ON vmo.id = g.model_id
    JOIN vehicle_makes vm   ON vm.id = vmo.make_id
    WHERE l.is_archived = 0
    GROUP BY vm.name, strftime('%Y-%m', l.first_seen_at)
)
SELECT
    make,
    month,
    sample_size,
    avg_price,
    ROUND(
        100.0 * (avg_price - LAG(avg_price) OVER (PARTITION BY make ORDER BY month))
        / NULLIF(LAG(avg_price) OVER (PARTITION BY make ORDER BY month), 0),
        1
    ) AS pct_change_vs_prev_month
FROM monthly
ORDER BY make, month;
