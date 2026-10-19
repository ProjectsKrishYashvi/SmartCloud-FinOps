import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

REQUIRED_COLUMNS = [
    "tenant_id",
    "provider",
    "service",
    "usage",
    "cost",
    "timestamp",
    "source_instance",
]


def parse_row(raw: Dict[str, str]) -> Dict[str, str]:
    row = {col: (raw.get(col, "").strip()) for col in REQUIRED_COLUMNS}
    # Coerce types
    row["usage"] = str(float(row["usage"]) if row["usage"] else 0.0)
    row["cost"] = str(float(row["cost"]) if row["cost"] else 0.0)
    # Normalize timestamp to YYYY-MM format (partition key)
    try:
        dt = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        row["month"] = dt.strftime("%Y-%m")
    except Exception:
        row["month"] = "unknown"
    return row


def clean_file(input_path: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with input_path.open("r", newline="", encoding="utf-8") as f_in, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as f_out:
        reader = csv.DictReader(f_in)
        fieldnames: List[str] = REQUIRED_COLUMNS + ["month"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for raw in reader:
            row = parse_row(raw)
            writer.writerow(row)
            count += 1
    return count


def main():
    input_dir = Path(os.environ.get("INPUT_DIR", "data-samples"))
    output_dir = Path(os.environ.get("OUTPUT_DIR", "outputs/processed"))
    processed = 0
    for name in ["azure_billing_sample.csv", "gcp_billing_sample.csv"]:
        in_path = input_dir / name
        if in_path.exists():
            out_path = output_dir / name.replace("_billing_sample", "_cleaned")
            processed += clean_file(in_path, out_path)
    print(f"Rows processed: {processed}")


if __name__ == "__main__":
    main() 