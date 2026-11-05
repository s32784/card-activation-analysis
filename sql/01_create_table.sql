-- 01_create_table.sql
-- Creates the customer table. One row = one credit card customer.
-- The two "Naive_Bayes_Classifier..." columns from the raw CSV are NOT loaded:
-- they are predictions from someone else's model, not customer data.
-- Written for SQLite; the same DDL runs on PostgreSQL (INTEGER/REAL/TEXT are valid there too).

DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    CLIENTNUM                 INTEGER PRIMARY KEY,  -- customer ID
    Attrition_Flag            TEXT,     -- 'Existing Customer' / 'Attrited Customer'
    Customer_Age              INTEGER,
    Gender                    TEXT,
    Dependent_count           INTEGER,
    Education_Level           TEXT,
    Marital_Status            TEXT,
    Income_Category           TEXT,
    Card_Category             TEXT,     -- Blue / Silver / Gold / Platinum
    Months_on_book            INTEGER,  -- tenure in months
    Total_Relationship_Count  INTEGER,  -- number of products held with the bank
    Months_Inactive_12_mon    INTEGER,  -- months with no activity in the last 12
    Contacts_Count_12_mon     INTEGER,  -- contacts with the bank in the last 12 months
    Credit_Limit              REAL,
    Total_Revolving_Bal       REAL,
    Avg_Open_To_Buy           REAL,     -- credit limit minus revolving balance
    Total_Amt_Chng_Q4_Q1      REAL,     -- spend in Q4 / spend in Q1
    Total_Trans_Amt           REAL,     -- total spend, last 12 months
    Total_Trans_Ct            INTEGER,  -- number of transactions, last 12 months
    Total_Ct_Chng_Q4_Q1       REAL,     -- transactions in Q4 / transactions in Q1
    Avg_Utilization_Ratio     REAL      -- revolving balance / credit limit
);
