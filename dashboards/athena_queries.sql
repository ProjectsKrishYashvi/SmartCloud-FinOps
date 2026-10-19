-- Create database (run once)
CREATE DATABASE IF NOT EXISTS finops;

-- Non-partitioned external table over processed CSVs in S3
-- Points to processed prefix to avoid picking up raw files
CREATE EXTERNAL TABLE IF NOT EXISTS finops.processed_costs (
  tenant_id string,
  provider string,
  service string,
  usage double,
  cost double,
  timestamp string,
  source_instance string,
  month string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
LOCATION 's3://smartcloud-finops-krish/tenants/tenantA/processed/'
TBLPROPERTIES ("skip.header.line.count"="1");

-- Spend by provider and service for a tenant/month
SELECT provider, service, sum(cost) as total_cost
FROM finops.processed_costs
WHERE tenant_id = 'tenantA' AND month = '2024-07'
GROUP BY provider, service
ORDER BY total_cost DESC;

-- Top costly services overall
SELECT service, sum(cost) as total_cost
FROM finops.processed_costs
GROUP BY service
ORDER BY total_cost DESC
LIMIT 10; 