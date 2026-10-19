# SmartCloud FinOps: AI-Based Multi-Cloud Cost Optimizer & Smart Deployment Orchestrator

A smart cloud assistant that ingests Azure/GCP billing data into AWS, analyzes and estimates the cost on AWS, provides savings recommendations, and includes a Smart Cloud Selector that can deploy new workloads to the most cost-effective cloud (AWS/Azure/GCP) using Terraform.

## Repo Structure

```
smartcloud-finops/
├─ data-samples/
├─ glue/
│  ├─ crawler-config/
│  └─ jobs/
├─ lambdas/
│  ├─ ingest/
│  ├─ simulate_aws_cost/
│  └─ recommend/
├─ selector/
├─ terraform/
│  ├─ aws/
│  ├─ azure/
│  └─ gcp/
├─ dashboards/
├─ mappings/
├─ docs/
└─ scripts/
```

## Quickstart (High-Level)

- Create an AWS account (free tier) and an S3 bucket (e.g., `smartcloud-finops-<yourid>`).
- Upload sample Azure/GCP billing CSVs to `s3://<bucket>/tenants/<tenantId>/raw/<provider>/YYYY-MM/`.
- Use Glue Crawler to catalog raw data; run Glue job to normalize to `processed/`.
- Query with Athena; build a QuickSight dashboard (trial) for visuals.
- Run the cost simulation Lambda to produce AWS savings recommendations per tenant.
- Use the Smart Cloud Selector (CLI) to choose a provider, then `terraform apply` to deploy a tiny VM (destroy after demo).

See `docs/README.md` for full step-by-step instructions. 