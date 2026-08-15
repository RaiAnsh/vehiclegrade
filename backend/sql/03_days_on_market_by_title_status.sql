-- Business question: "Do salvage/rebuilt-title vehicles sit on the market
-- longer than clean-title ones - and by how much?" A real signal for buyers
-- (a long-listed car usually means it's overpriced or something's putting
-- buyers off) and for the business (which segments are hardest to move).
--
-- ROUND(..., 1) throughout for readable output - these are descriptive
-- stats for a report, not inputs to another calculation, so display
-- precision beats float precision here.

SELECT
    title_status,
    COUNT(*)                           AS sample_size,
    ROUND(AVG(days_listed), 1)         AS avg_days_listed,
    MIN(days_listed)                   AS min_days_listed,
    MAX(days_listed)                   AS max_days_listed,
    ROUND(AVG(price), 2)               AS avg_price
FROM listings
WHERE is_archived = 0
GROUP BY title_status
ORDER BY avg_days_listed DESC;
