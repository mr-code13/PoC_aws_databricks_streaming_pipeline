%sql
-- 1. SWITCH CONTEXT: Use your actual Unity Catalog.
USE CATALOG workspace;

-- 2. CREATE SCHEMA: Creates the managed schema. 
CREATE SCHEMA IF NOT EXISTS data_staging
-- substitute 'yourbucketname' with your actual bucket name
MANAGED LOCATION 's3://yourbucketnamehere/unity-catalog/data_staging';

-- 3. VERIFY: Confirm the new schema exists inside your catalog.
SHOW SCHEMAS IN workspace;