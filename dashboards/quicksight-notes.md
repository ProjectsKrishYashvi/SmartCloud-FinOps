# QuickSight Dashboard Notes

Datasets:
- Athena table: `finops.processed_costs`

Recommended visuals:
- KPI: Total Spend (filter by `tenant_id`, `month`)
- Bar: Spend by Provider
- Bar: Spend by Service
- Line: Monthly Spend Trend
- Table: Potential AWS Savings (ingest from `outputs/recommendations/*_aws_savings.json` via S3 dataset)

Filters/Controls:
- `tenant_id` (drop-down)
- `month` (drop-down)

Tips:
- Use parameterized dataset to pass `tenant_id` into analyses.
- Duplicate the dashboard per tenant if needed. 