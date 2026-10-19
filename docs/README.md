# SmartCloud FinOps - Full Setup Guide (Free Tier)

This guide walks you through an end-to-end setup on AWS using only free-tier resources wherever possible. All commands are PowerShell-friendly on Windows.

## Prerequisites
- AWS Account (free tier) and IAM admin user
- AWS CLI v2 configured: `aws configure`
- Python 3.10+ in PATH: `python --version`
- Terraform 1.6+ in PATH: `terraform -version`
- Optional: Azure (free trial) and GCP (free tier) accounts for the selector demo

## QuickSight Note
QuickSight Standard trial is 30 days only. Save it for when you need to present the dashboard. For now, we'll focus on the core pipeline and Terraform deployments.

## 1) Clone repo and create a Python venv (optional)
```powershell
cd C:\CloudProj
# If repo not already created by Cursor, create dirs
mkdir smartcloud-finops -Force | Out-Null
# (You already have files via Cursor; skip clone.)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
```

## 2) Prepare S3 bucket and folder layout
- Pick a unique bucket name: `smartcloud-finops-<yourid>`
```powershell
$Bucket = "smartcloud-finops-$env:USERNAME"
aws s3 mb s3://$Bucket
```

Folder layout we will use:
- `s3://$Bucket/tenants/tenantA/raw/2024-07/` (input)
- `s3://$Bucket/tenants/tenantA/processed/2024-07/` (output later)

Upload local sample CSVs (provided in `data-samples/`):
```powershell
cd smartcloud-finops
python .\scripts\seed_to_s3.py --bucket $Bucket --tenant tenantA --month 2024-07
```

## 3) Run ETL locally first (simulates Glue Job)
This normalizes CSVs and produces cleaned outputs under `outputs/processed`.
```powershell
$env:INPUT_DIR = "data-samples"
$env:OUTPUT_DIR = "outputs/processed"
python .\glue\jobs\clean_transform.py
```

(If you prefer Glue later: upload cleaned files to `s3://$Bucket/tenants/tenantA/processed/2024-07/` and create a Crawler pointing to `s3://$Bucket/tenants/`.)

Upload cleaned files to S3 for Athena:
```powershell
aws s3 sync .\outputs\processed s3://$Bucket/tenants/tenantA/processed/2024-07/ --exclude "*" --include "*_cleaned.csv"
```

## 4) Athena database, table, and queries
Open the Athena console and select your S3 query results location (use a new bucket or a folder in `$Bucket`).
- In the query editor, run the statements in `dashboards/athena_queries.sql`.
- Replace `YOUR_BUCKET` with your bucket name in the table `LOCATION` before running the CREATE TABLE.
- After uploading processed data, run `MSCK REPAIR TABLE finops.processed_costs;`.
- Test query: spend by provider/service for tenantA in `2024-07`.

## 5) Run AWS cost simulation and recommendations (locally)
```powershell
$env:MAPPING_FILE = "mappings/vm_mapping.csv"
$env:INPUT_DIR    = "outputs/processed"
$env:OUTPUT_DIR   = "outputs/recommendations"
python .\lambdas\simulate_aws_cost\handler.py
python .\lambdas\recommend\handler.py
Get-Content .\outputs\recommendations\tenantA_recommendations.txt
```
Outputs:
- JSON per-tenant: `outputs/recommendations/tenantA_aws_savings.json`
- Text summary: `outputs/recommendations/tenantA_recommendations.txt`

## 6) QuickSight dashboard (60-day trial) - SKIP FOR NOW
- Start QuickSight Standard trial when ready to present.
- Create data source: Athena → database `finops` → table `processed_costs`.
- Add controls: `tenant_id`, `month`.
- Add visuals per `dashboards/quicksight-notes.md`.
- Optional: Ingest `outputs/recommendations/*_aws_savings.json` into S3 and create a dataset for recommendations table.

## 7) Smart Cloud Selector (local)
```powershell
cd selector
python .\run_selector.py --region us-east-1 --app_type api --cost high --prices '{"aws":50,"azure":55,"gcp":60}' --load '{"aws":0.3,"azure":0.5,"gcp":0.2}'
cd ..
```
Expected output:
```json
{"provider": "aws", "reason": "Chose aws: lowest price (50)."}
```

## 8) Terraform demo deploy (pick only one cloud at a time)
Free-tier safety rules:
- Deploy only while demoing.
- Destroy immediately after.
- Use smallest instance types.

### 8a) AWS EC2 (free-tier eligible t2.micro)
```powershell
cd terraform\aws
$Region = "us-east-1"
# Generate or reuse an SSH key (public key only is needed)
ssh-keygen -t rsa -b 2048 -f "$HOME\.ssh\smartcloud_finops" -N ""
terraform init
terraform apply -auto-approve -var region=$Region -var public_key_path="$HOME\.ssh\smartcloud_finops.pub" -var tenant="tenantA"
# After apply, note outputs public_ip/public_dns
# Test in browser: http://<public_ip>
# Destroy when done
terraform destroy -auto-approve -var region=$Region -var public_key_path="$HOME\.ssh\smartcloud_finops.pub" -var tenant="tenantA"
cd ..\..
```

### 8b) Azure VM (Standard_B1s)
Requires Azure CLI login and a subscription (free trial works). Costs should be near free while running briefly.
```powershell
az login
cd terraform\azure
terraform init
terraform apply -auto-approve -var public_key_path="$HOME\.ssh\smartcloud_finops.pub" -var tenant="tenantA"
# Grab output public_ip; test http://<ip>
terraform destroy -auto-approve -var public_key_path="$HOME\.ssh\smartcloud_finops.pub" -var tenant="tenantA"
cd ..\..
```

### 8c) GCP VM (e2-micro)
Requires Google Cloud project and `gcloud auth application-default login`.
```powershell
gcloud auth application-default login
cd terraform\gcp
$GcpProject = "<your-gcp-project-id>"
terraform init
terraform apply -auto-approve -var project=$GcpProject -var tenant="tenantA"
# Test http://<public_ip>
terraform destroy -auto-approve -var project=$GcpProject -var tenant="tenantA"
cd ..\..
```

## 9) EventBridge schedules and IAM
- See `docs/eventbridge_iam.md` for least-privilege S3 access policy and schedule setup.
- Attach `AWSLambdaBasicExecutionRole` to Lambda roles.

## 10) Cleanup to avoid charges
- Destroy any Terraform stacks you created.
- Delete S3 objects and (optionally) the bucket.
- Stop/disable QuickSight if you don't need the trial running.

You now have an end-to-end MVP: ingest → normalize → query → simulate → recommend → visualize → select → deploy. 