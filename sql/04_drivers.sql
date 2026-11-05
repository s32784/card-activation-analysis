-- 04_drivers.sql
-- Drivers of low usage and churn. Descriptive comparisons only (no model).
-- "Attrition rate" = share of customers in the group with Attrition_Flag = 'Attrited Customer'.

-- name: attr_by_inactive
-- Question: does attrition rise with the number of inactive months?
SELECT
    Months_Inactive_12_mon                                      AS months_inactive,
    COUNT(*)                                                    AS n_customers,
    SUM(Attrition_Flag = 'Attrited Customer')                   AS n_attrited,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct
FROM customers
GROUP BY Months_Inactive_12_mon
ORDER BY Months_Inactive_12_mon;

-- name: attr_by_contacts
-- Question: are customers who contact the bank more often more likely to leave?
SELECT
    Contacts_Count_12_mon                                       AS contacts_12m,
    COUNT(*)                                                    AS n_customers,
    SUM(Attrition_Flag = 'Attrited Customer')                   AS n_attrited,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct
FROM customers
GROUP BY Contacts_Count_12_mon
ORDER BY Contacts_Count_12_mon;

-- name: attr_by_card
-- Question: does attrition differ by card tier? How much does each tier spend?
SELECT
    Card_Category                                               AS card_category,
    COUNT(*)                                                    AS n_customers,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct,
    ROUND(AVG(Total_Trans_Amt), 0)                              AS avg_spend,
    ROUND(AVG(Total_Trans_Ct), 1)                               AS avg_transactions
FROM customers
GROUP BY Card_Category
ORDER BY avg_spend;

-- name: attr_by_income
-- Question: does attrition differ by income band?
SELECT
    Income_Category                                             AS income_category,
    COUNT(*)                                                    AS n_customers,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct
FROM customers
GROUP BY Income_Category
ORDER BY attrition_rate_pct DESC;

-- name: attr_by_age
-- Question: does attrition differ by age band?
WITH banded AS (
    SELECT *,
        CASE
            WHEN Customer_Age < 35 THEN '1. <35'
            WHEN Customer_Age < 45 THEN '2. 35-44'
            WHEN Customer_Age < 55 THEN '3. 45-54'
            ELSE '4. 55+'
        END AS age_band
    FROM customers
)
SELECT
    age_band,
    COUNT(*)                                                    AS n_customers,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct
FROM banded
GROUP BY age_band
ORDER BY age_band;

-- name: activity_change_by_status
-- Question: did churned customers already reduce their card use (Q4 vs Q1) before leaving?
-- The median is computed with window functions: ROW_NUMBER numbers customers from lowest to
-- highest change inside each group (PARTITION BY), COUNT(*) OVER gives the group size,
-- and we keep the middle row(s).
WITH ranked AS (
    SELECT
        Attrition_Flag,
        Total_Ct_Chng_Q4_Q1,
        ROW_NUMBER() OVER (PARTITION BY Attrition_Flag ORDER BY Total_Ct_Chng_Q4_Q1) AS rn,
        COUNT(*)     OVER (PARTITION BY Attrition_Flag)                              AS n
    FROM customers
),
medians AS (
    SELECT Attrition_Flag, AVG(Total_Ct_Chng_Q4_Q1) AS median_ct_change
    FROM ranked
    WHERE rn IN ((n + 1) / 2, (n + 2) / 2)   -- middle row (odd n) or two middle rows (even n)
    GROUP BY Attrition_Flag
)
SELECT
    c.Attrition_Flag                                            AS status,
    COUNT(*)                                                    AS n_customers,
    ROUND(AVG(c.Total_Ct_Chng_Q4_Q1), 2)                        AS avg_ct_change_q4_q1,
    ROUND(m.median_ct_change, 2)                                AS median_ct_change_q4_q1,
    ROUND(AVG(c.Total_Amt_Chng_Q4_Q1), 2)                       AS avg_amt_change_q4_q1,
    ROUND(100.0 * AVG(c.Total_Ct_Chng_Q4_Q1 < 0.6), 1)          AS pct_trans_down_40pct_plus,
    ROUND(AVG(c.Total_Trans_Ct), 1)                             AS avg_transactions,
    ROUND(AVG(c.Total_Trans_Amt), 0)                            AS avg_spend,
    ROUND(AVG(c.Avg_Utilization_Ratio), 3)                      AS avg_utilization
FROM customers c
JOIN medians m ON m.Attrition_Flag = c.Attrition_Flag
GROUP BY c.Attrition_Flag, m.median_ct_change
ORDER BY status;

-- name: ct_change_distribution
-- Question: how are churned vs retained customers spread across bands of Q4-vs-Q1 transaction change?
WITH banded AS (
    SELECT
        Attrition_Flag,
        CASE
            WHEN Total_Ct_Chng_Q4_Q1 < 0.4 THEN '1. down >60%'
            WHEN Total_Ct_Chng_Q4_Q1 < 0.6 THEN '2. down 40-60%'
            WHEN Total_Ct_Chng_Q4_Q1 < 0.8 THEN '3. down 20-40%'
            WHEN Total_Ct_Chng_Q4_Q1 < 1.0 THEN '4. down 0-20%'
            ELSE '5. flat or up'
        END AS ct_change_band
    FROM customers
)
SELECT
    ct_change_band,
    Attrition_Flag AS status,
    COUNT(*) AS n_customers,
    -- share of the status group (all churned = 100%, all retained = 100%)
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY Attrition_Flag), 1) AS pct_of_status
FROM banded
GROUP BY ct_change_band, Attrition_Flag
ORDER BY ct_change_band, status;

-- name: attr_by_ct_change_band
-- Question: what is the attrition rate in each band of Q4-vs-Q1 transaction change?
SELECT
    CASE
        WHEN Total_Ct_Chng_Q4_Q1 < 0.4 THEN '1. down >60%'
        WHEN Total_Ct_Chng_Q4_Q1 < 0.6 THEN '2. down 40-60%'
        WHEN Total_Ct_Chng_Q4_Q1 < 0.8 THEN '3. down 20-40%'
        WHEN Total_Ct_Chng_Q4_Q1 < 1.0 THEN '4. down 0-20%'
        ELSE '5. flat or up'
    END AS ct_change_band,
    COUNT(*)                                                    AS n_customers,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct
FROM customers
GROUP BY ct_change_band
ORDER BY ct_change_band;

-- name: utilization_by_segment
-- Question: how much of their credit limit do customers in each segment use, churned vs retained?
SELECT
    segment,
    Attrition_Flag                          AS status,
    COUNT(*)                                AS n_customers,
    ROUND(AVG(Avg_Utilization_Ratio), 3)    AS avg_utilization,
    ROUND(100.0 * AVG(Total_Revolving_Bal = 0), 1) AS pct_zero_revolving_balance
FROM customer_segments
GROUP BY segment, Attrition_Flag
ORDER BY segment, status;

-- name: early_warning_combo
-- Question: if the bank flags customers with 3+ inactive months AND 3+ contacts, how risky is that group?
SELECT
    CASE WHEN Months_Inactive_12_mon >= 3 AND Contacts_Count_12_mon >= 3
         THEN 'Flagged: 3+ inactive months and 3+ contacts'
         ELSE 'Not flagged' END                                  AS group_name,
    COUNT(*)                                                    AS n_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct_of_base,
    SUM(Attrition_Flag = 'Attrited Customer')                   AS n_attrited,
    ROUND(100.0 * SUM(Attrition_Flag = 'Attrited Customer')
          / SUM(SUM(Attrition_Flag = 'Attrited Customer')) OVER (), 1) AS pct_of_all_attrited,
    ROUND(100.0 * AVG(Attrition_Flag = 'Attrited Customer'), 1) AS attrition_rate_pct
FROM customers
GROUP BY group_name
ORDER BY group_name;

-- name: segment_by_card
-- Question: how do segments split across card tiers? (source for the Excel pivot)
SELECT
    segment,
    Card_Category                    AS card_category,
    COUNT(*)                         AS n_customers,
    ROUND(AVG(Total_Trans_Amt), 0)   AS avg_spend
FROM customer_segments
GROUP BY segment, Card_Category
ORDER BY segment, card_category;
