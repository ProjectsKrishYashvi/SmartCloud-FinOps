#!/usr/bin/env python3
"""
Hybrid Recommender CLI
Usage: python recommend_hybrid.py --tenant tenantA [--compare] [--billing inputs/billing_tenantA.csv]
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from lambdas.recommend.hybrid_recommender import main

def cli():
    parser = argparse.ArgumentParser(
        description="SmartCloud FinOps Hybrid Recommender System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python recommend_hybrid.py --tenant tenantA
  python recommend_hybrid.py --tenant tenantA --compare
  python recommend_hybrid.py --tenant tenantA --billing inputs/billing_tenantA.csv --compare
        """
    )

    parser.add_argument("--tenant", type=str, help="Specific tenant to process (default: all tenants)")
    parser.add_argument("--region", type=str, default="us-east-1",
                        choices=["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "ap-southeast-1"],
                        help="Region for recommendations (default: us-east-1)")
    parser.add_argument("--cost-sensitivity", type=str, default="medium",
                        choices=["high", "medium", "low"], help="Cost sensitivity level (default: medium)")
    parser.add_argument("--show-top", type=int, default=5, help="Number of top recommendations to show")
    parser.add_argument("--compare", action="store_true", help="Show comparison between rule-based and ML decisions")
    parser.add_argument("--billing", type=str, help="Path to billing CSV (tenant-level)")

    args = parser.parse_args()

    print("SmartCloud FinOps Hybrid Recommender")
    print("=" * 50)
    print(f"Tenant: {args.tenant or 'All'}")
    print(f"Region: {args.region}")
    print(f"Cost Sensitivity: {args.cost_sensitivity}")
    print(f"Show Comparison: {args.compare}")
    if args.billing:
        print(f"Billing CSV: {args.billing}")
    print("=" * 50)

    main(args.tenant, args.compare)

if __name__ == "__main__":
    cli()
