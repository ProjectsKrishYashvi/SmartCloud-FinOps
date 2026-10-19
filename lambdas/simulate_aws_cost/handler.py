import csv
import json
import os
from pathlib import Path
from typing import Dict, List

MAPPING_FILE = Path(os.environ.get("MAPPING_FILE", "mappings/vm_mapping.csv"))
INPUT_DIR = Path(os.environ.get("INPUT_DIR", "outputs/processed"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "outputs/recommendations"))


def load_mapping() -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    if not MAPPING_FILE.exists():
        return mapping
    with MAPPING_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['provider']}::{row['source_instance']}"
            mapping[key] = row
    return mapping


def simulate_for_file(cleaned_csv: Path, mapping: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    with cleaned_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("service") != "Compute":
                continue
            key = f"{row['provider']}::{row.get('source_instance','')}"
            mapped = mapping.get(key)
            if not mapped:
                continue
            est_aws = float(mapped.get("estimated_aws_monthly", "0") or 0)
            current_cost = float(row.get("cost", "0") or 0)
            savings = current_cost - est_aws
            results.append(
                {
                    "tenant_id": row["tenant_id"],
                    "provider": row["provider"],
                    "source_instance": row.get("source_instance", ""),
                    "aws_equivalent": mapped.get("aws_equivalent", "unknown"),
                    "current_monthly_cost": current_cost,
                    "estimated_aws_monthly": est_aws,
                    "estimated_monthly_savings": savings,
                    "month": row.get("month", "unknown"),
                }
            )
    return results


def write_results(tenant_id: str, items: List[Dict[str, str]]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{tenant_id}_aws_savings.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def handler(event, context):
    mapping = load_mapping()
    aggregated: Dict[str, List[Dict[str, str]]] = {}
    for file in INPUT_DIR.glob("*_cleaned.csv"):
        items = simulate_for_file(file, mapping)
        for it in items:
            aggregated.setdefault(it["tenant_id"], []).append(it)
    for tenant_id, items in aggregated.items():
        write_results(tenant_id, items)
    return {"status": "ok", "tenants": list(aggregated.keys())}


if __name__ == "__main__":
    print(handler({}, {})) 