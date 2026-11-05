-- 03_segmentation.sql
-- RFM-style activity segmentation.
--
-- The data has no "last purchase date", so we build the three RFM dimensions from what exists:
--   R (recency proxy) = Months_Inactive_12_mon   -> fewer inactive months = better
--   F (frequency)     = Total_Trans_Ct           -> more transactions = better
--   M (monetary)      = Total_Trans_Amt          -> more spend = better
-- Every score runs 1 (worst) to 4 (best).
--
-- F and M: NTILE(4) splits customers into 4 equal-sized groups (quartiles) by rank.
-- R: Months_Inactive only takes the values 0-6 and 38% of customers have exactly 3.
--    NTILE(4) would cut through a block of identical customers and give some of them R=1
--    and others R=2 at random. So R uses fixed bands instead (see dq_inactive_distribution):
--      R=4: 0-1 months inactive, R=3: 2 months, R=2: 3 months, R=1: 4+ months.

-- name: build_segments
-- Question: which RFM scores and which activity segment does each customer get?
DROP TABLE IF EXISTS customer_segments;

CREATE TABLE customer_segments AS
WITH scores AS (
    SELECT
        c.*,
        CASE
            WHEN Months_Inactive_12_mon <= 1 THEN 4
            WHEN Months_Inactive_12_mon = 2  THEN 3
            WHEN Months_Inactive_12_mon = 3  THEN 2
            ELSE 1
        END AS r_score,
        -- window function: rank all customers by transaction count, cut into 4 equal groups
        NTILE(4) OVER (ORDER BY Total_Trans_Ct, CLIENTNUM)  AS f_score,
        NTILE(4) OVER (ORDER BY Total_Trans_Amt, CLIENTNUM) AS m_score
    FROM customers c
)
SELECT
    *,
    -- Rules are checked top to bottom; a customer gets the FIRST segment whose rule matches.
    CASE
        WHEN f_score = 4 AND m_score = 4 AND r_score >= 3
            THEN '1. Champions'      -- top 25% on both transactions and spend, and active recently
        WHEN r_score <= 2 AND Total_Ct_Chng_Q4_Q1 < 0.6
            THEN '2. At risk'        -- 3+ inactive months AND Q4 transactions down 40%+ vs Q1
        WHEN f_score = 1 AND m_score = 1
            THEN '3. Dormant'        -- bottom 25% on both transactions and spend
        WHEN f_score + m_score <= 4
            THEN '4. Low-activity'   -- below-median usage overall, but not in the bottom on both
        ELSE '5. Steady users'       -- everyone else: medium usage, no warning signs
    END AS segment
FROM scores;

-- name: segment_summary
-- Question: how big is each segment, how does it use the card, and how many customers did it lose?
SELECT
    segment,
    COUNT(*)                                                    AS n_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct_of_base,
    ROUND(AVG(Total_Trans_Amt), 0)                              AS avg_spend,
    ROUND(AVG(Total_Trans_Ct), 1)                               AS avg_transactions,
    ROUND(AVG(Months_Inactive_12_mon), 2)                       AS avg_months_inactive,
    ROUND(AVG(Total_Ct_Chng_Q4_Q1), 2)                          AS avg_ct_change_q4_q1,
    ROUND(AVG(Avg_Utilization_Ratio), 3)                        AS avg_utilization,
    SUM(Attrition_Flag = 'Attrited Customer')                   AS n_attrited,
    -- share of ALL churned customers that sit in this segment
    ROUND(100.0 * SUM(Attrition_Flag = 'Attrited Customer')
          / SUM(SUM(Attrition_Flag = 'Attrited Customer')) OVER (), 1) AS pct_of_all_attrited,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct
FROM customer_segments
GROUP BY segment
ORDER BY segment;

-- name: score_boundaries
-- Question: which raw values does each F and M quartile cover? (to explain the scores in plain numbers)
SELECT 'F (transactions)' AS dimension, f_score AS score,
       MIN(Total_Trans_Ct) AS min_value, MAX(Total_Trans_Ct) AS max_value, COUNT(*) AS n_customers
FROM customer_segments GROUP BY f_score
UNION ALL
SELECT 'M (spend)', m_score, MIN(Total_Trans_Amt), MAX(Total_Trans_Amt), COUNT(*)
FROM customer_segments GROUP BY m_score
UNION ALL
SELECT 'R (recency bands)', r_score, MIN(Months_Inactive_12_mon), MAX(Months_Inactive_12_mon), COUNT(*)
FROM customer_segments GROUP BY r_score
ORDER BY dimension, score;
