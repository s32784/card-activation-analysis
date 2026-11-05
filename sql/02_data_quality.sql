-- 02_data_quality.sql
-- Data quality checks. Each named query is saved to data/processed/dq_<name>.csv.

-- name: dq_row_count
-- Question: how many customers did we load, and how many churned?
SELECT
    COUNT(*)                                                        AS n_customers,
    SUM(CASE WHEN Attrition_Flag = 'Attrited Customer' THEN 1 ELSE 0 END) AS n_attrited,
    ROUND(100.0 * AVG(CASE WHEN Attrition_Flag = 'Attrited Customer' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM customers;

-- name: dq_duplicates
-- Question: is CLIENTNUM unique (one row per customer)?
SELECT
    COUNT(*)                  AS n_rows,
    COUNT(DISTINCT CLIENTNUM) AS n_distinct_clients,
    COUNT(*) - COUNT(DISTINCT CLIENTNUM) AS n_duplicates
FROM customers;

-- name: dq_missing_unknown
-- Question: how many missing (NULL) or 'Unknown' values does each text column have?
SELECT 'Education_Level' AS column_name,
       SUM(Education_Level IS NULL) AS n_null,
       SUM(Education_Level = 'Unknown') AS n_unknown
FROM customers
UNION ALL
SELECT 'Marital_Status', SUM(Marital_Status IS NULL), SUM(Marital_Status = 'Unknown') FROM customers
UNION ALL
SELECT 'Income_Category', SUM(Income_Category IS NULL), SUM(Income_Category = 'Unknown') FROM customers
UNION ALL
SELECT 'Gender', SUM(Gender IS NULL), SUM(Gender = 'Unknown') FROM customers
UNION ALL
SELECT 'Card_Category', SUM(Card_Category IS NULL), SUM(Card_Category = 'Unknown') FROM customers;

-- name: dq_nulls_numeric
-- Question: are there NULLs in the numeric columns we use for scoring?
SELECT
    SUM(Months_Inactive_12_mon IS NULL) AS null_inactive,
    SUM(Contacts_Count_12_mon IS NULL)  AS null_contacts,
    SUM(Total_Trans_Amt IS NULL)        AS null_trans_amt,
    SUM(Total_Trans_Ct IS NULL)         AS null_trans_ct,
    SUM(Total_Ct_Chng_Q4_Q1 IS NULL)    AS null_ct_chng,
    SUM(Avg_Utilization_Ratio IS NULL)  AS null_util
FROM customers;

-- name: dq_ranges
-- Question: are values in a plausible range? (no negative amounts, utilization between 0 and 1)
SELECT
    MIN(Customer_Age) AS min_age,            MAX(Customer_Age) AS max_age,
    MIN(Months_Inactive_12_mon) AS min_inactive, MAX(Months_Inactive_12_mon) AS max_inactive,
    MIN(Contacts_Count_12_mon) AS min_contacts,  MAX(Contacts_Count_12_mon) AS max_contacts,
    MIN(Credit_Limit) AS min_limit,          MAX(Credit_Limit) AS max_limit,
    MIN(Total_Trans_Amt) AS min_spend,       MAX(Total_Trans_Amt) AS max_spend,
    MIN(Total_Trans_Ct) AS min_trans,        MAX(Total_Trans_Ct) AS max_trans,
    MIN(Avg_Utilization_Ratio) AS min_util,  MAX(Avg_Utilization_Ratio) AS max_util,
    SUM(Total_Trans_Amt < 0 OR Credit_Limit < 0 OR Total_Revolving_Bal < 0) AS n_negative_amounts,
    SUM(Avg_Utilization_Ratio < 0 OR Avg_Utilization_Ratio > 1) AS n_util_out_of_range
FROM customers;

-- name: dq_open_to_buy
-- Question: is Avg_Open_To_Buy consistent with Credit_Limit - Total_Revolving_Bal?
SELECT
    SUM(ABS(Credit_Limit - Total_Revolving_Bal - Avg_Open_To_Buy) > 1) AS n_inconsistent
FROM customers;

-- name: dq_inactive_distribution
-- Question: how are customers spread across months inactive? (needed to choose the recency bands)
SELECT
    Months_Inactive_12_mon,
    COUNT(*) AS n_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_base
FROM customers
GROUP BY Months_Inactive_12_mon
ORDER BY Months_Inactive_12_mon;
