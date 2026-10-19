import argparse
import os
import pathlib
import subprocess
from typing import List


def sync_folder_to_s3(local_folder: str, bucket: str, prefix: str):
    src = pathlib.Path(local_folder)
    if not src.exists():
        print(f"Skipping missing folder: {src}")
        return
    dest = f"s3://{bucket}/{prefix}"
    cmd = [
        "aws",
        "s3",
        "sync",
        str(src),
        dest,
        "--exclude",
        "*",
        "--include",
        "*.csv",
    ]
    print(" ".join(cmd))
    subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Seed S3 with sample billing data")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--tenant", default="tenantA")
    parser.add_argument("--month", default="2024-07")
    args = parser.parse_args()

    base_prefix = f"tenants/{args.tenant}"
    sync_folder_to_s3("data-samples", args.bucket, f"{base_prefix}/raw/{args.month}")
    print("Done.")


if __name__ == "__main__":
    main() 