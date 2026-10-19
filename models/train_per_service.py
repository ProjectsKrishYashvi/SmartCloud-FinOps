import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
from sklearn.calibration import CalibratedClassifierCV
import joblib
import json
from pathlib import Path
import random

# Try to import XGBoost, fallback to GradientBoosting if not available
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available, using GradientBoostingClassifier")

PROVIDERS = ["aws", "azure", "gcp"]
REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "ap-southeast-1"]

random.seed(42)
np.random.seed(42)


def _noise(value: float, pct: float = 0.15) -> float:
    return value * (1 + random.uniform(-pct, pct))


def gen_compute_samples(n: int = 100000) -> pd.DataFrame:
    """
    Generate training data that ALIGNS with rule-based logic.
    The key insight: ML should learn the SAME patterns as rules, not contradict them.
    """
    rows = []
    for _ in range(n):
        region = random.choice(REGIONS)
        usage_hours = max(1.0, _noise(random.uniform(50, 800)))
        on_demand_ratio = min(1.0, max(0.0, _noise(random.uniform(0.3, 1.0), 0.2)))
        reserved_ratio = 1.0 - on_demand_ratio
        weekday_vs_weekend_ratio = min(5.0, max(0.2, _noise(random.uniform(0.5, 3.0), 0.2)))
        instance_family = random.choice(["general", "compute", "memory"])
        
        # Base costs with realistic pricing - AWS is typically cheapest for compute
        base_aws_cost = usage_hours * (0.12 * on_demand_ratio + 0.08 * reserved_ratio)  # AWS cheapest
        base_azure_cost = usage_hours * (0.15 * on_demand_ratio + 0.10 * reserved_ratio)  # Azure more expensive
        base_gcp_cost = usage_hours * (0.14 * on_demand_ratio + 0.09 * reserved_ratio)   # GCP middle
        
        monthly_costs = {
            "aws": _noise(base_aws_cost),
            "azure": _noise(base_azure_cost),
            "gcp": _noise(base_gcp_cost),
        }
        
        # Business requirements
        cost_sensitivity = random.choice(["high", "medium", "low"])
        compliance_required = 1 if (region in ["eu-west-1", "us-east-1"] and random.random() < 0.3) else 0
        performance_priority = 1 if (random.random() < 0.25) else 0
        data_sovereignty = 1 if (region in ["eu-west-1", "ap-south-1"] and random.random() < 0.2) else 0
        
        # CRITICAL: AWS is typically the best choice for compute (cheapest + reliable)
        # This matches the rule-based logic that AWS is chosen
        best = "aws"  # Default to AWS for compute
        
        # Only override in specific cases
        if compliance_required and region in ["eu-west-1"]:
            best = "azure"  # Azure for EU compliance
        elif performance_priority and monthly_costs["gcp"] < monthly_costs["aws"] * 0.9:
            best = "gcp"   # GCP only if significantly cheaper for performance
        elif cost_sensitivity == "high" and monthly_costs["gcp"] < monthly_costs["aws"] * 0.85:
            best = "gcp"   # GCP only if much cheaper

        rows.append({
            "usage_hours": usage_hours,
            "monthly_cost": monthly_costs[best],
            "on_demand_ratio": on_demand_ratio,
            "reserved_ratio": reserved_ratio,
            "weekday_vs_weekend_ratio": weekday_vs_weekend_ratio,
            "region": region,
            "instance_family": instance_family,
            "cost_sensitivity": cost_sensitivity,
            "compliance_required": compliance_required,
            "performance_priority": performance_priority,
            "data_sovereignty": data_sovereignty,
            "aws_cost": monthly_costs["aws"],
            "azure_cost": monthly_costs["azure"], 
            "gcp_cost": monthly_costs["gcp"],
            "best_provider": best,
        })
    return pd.DataFrame(rows)


def gen_storage_samples(n: int = 100000) -> pd.DataFrame:
    rows = []
    for _ in range(n):
        region = random.choice(REGIONS)
        storage_gb = max(1.0, _noise(random.uniform(50, 50000)))
        total_requests = max(0, int(_noise(random.uniform(1000, 1000000))))
        read_ratio = min(1.0, max(0.0, _noise(random.uniform(0.5, 0.95), 0.2)))
        write_ratio = 1.0 - read_ratio
        cold_vs_hot_ratio = min(1.0, max(0.0, _noise(random.uniform(0.1, 0.9), 0.2)))
        monthly_costs = {
            "aws": _noise(storage_gb * (0.024 * (1 - cold_vs_hot_ratio) + 0.012 * cold_vs_hot_ratio) + total_requests * (0.000004 * read_ratio + 0.000005 * write_ratio)),
            "azure": _noise(storage_gb * (0.023 * (1 - cold_vs_hot_ratio) + 0.011 * cold_vs_hot_ratio) + total_requests * (0.0000045 * read_ratio + 0.000005 * write_ratio)),
            "gcp": _noise(storage_gb * (0.022 * (1 - cold_vs_hot_ratio) + 0.010 * cold_vs_hot_ratio) + total_requests * (0.0000035 * read_ratio + 0.0000045 * write_ratio)),
        }
        cost_sensitivity = random.choice(["high", "medium", "low"])
        data_sovereignty = 1 if (region == "ap-south-1" and random.random() < 0.2) else 0
        best = min(monthly_costs, key=monthly_costs.get)
        if data_sovereignty and region == "ap-south-1":
            best = "gcp"
        rows.append({
            "storage_gb": storage_gb,
            "requests": total_requests,
            "read_ratio": read_ratio,
            "write_ratio": write_ratio,
            "cold_vs_hot_ratio": cold_vs_hot_ratio,
            "monthly_cost": min(monthly_costs.values()),
            "region": region,
            "cost_sensitivity": cost_sensitivity,
            "data_sovereignty": data_sovereignty,
            "best_provider": best,
        })
    return pd.DataFrame(rows)


def gen_database_samples(n: int = 100000) -> pd.DataFrame:
    rows = []
    for _ in range(n):
        region = random.choice(REGIONS)
        db_storage_gb = max(1.0, _noise(random.uniform(20, 10000)))
        db_usage_hours = max(1.0, _noise(random.uniform(50, 720)))
        iops_estimate = max(100, int(_noise(random.uniform(100, 40000))))
        read_write_mix = min(1.0, max(0.0, _noise(random.uniform(0.4, 0.9), 0.2)))
        multi_az = 1 if random.random() < 0.3 else 0
        monthly_costs = {
            "aws": _noise(db_storage_gb * 0.12 + db_usage_hours * 0.30 + iops_estimate * 0.00002 + (0.15 if multi_az else 0)),
            "azure": _noise(db_storage_gb * 0.11 + db_usage_hours * 0.28 + iops_estimate * 0.000025 + (0.10 if multi_az else 0)),
            "gcp": _noise(db_storage_gb * 0.10 + db_usage_hours * 0.29 + iops_estimate * 0.000022 + (0.12 if multi_az else 0)),
        }
        cost_sensitivity = random.choice(["high", "medium", "low"])
        compliance_required = 1 if (region == "eu-west-1" and random.random() < 0.2) else 0
        best = min(monthly_costs, key=monthly_costs.get)
        if compliance_required and region == "eu-west-1":
            best = "azure"
        rows.append({
            "db_storage_gb": db_storage_gb,
            "db_usage_hours": db_usage_hours,
            "iops_estimate": iops_estimate,
            "read_write_mix": read_write_mix,
            "multi_az": multi_az,
            "monthly_cost": min(monthly_costs.values()),
            "region": region,
            "cost_sensitivity": cost_sensitivity,
            "compliance_required": compliance_required,
            "best_provider": best,
        })
    return pd.DataFrame(rows)


def _encode_categoricals(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    return pd.get_dummies(df, columns=cols, drop_first=False)


def _train_and_save(df: pd.DataFrame, label: str, model_path: Path, meta_path: Path):
    feature_cols = [c for c in df.columns if c != label]
    X = df[feature_cols].values
    y = df[label].map({"aws": 0, "azure": 1, "gcp": 2}).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Use XGBoost if available, otherwise GradientBoosting
    if XGBOOST_AVAILABLE:
        base = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='mlogloss'
        )
    else:
        base = GradientBoostingClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
    
    model = CalibratedClassifierCV(estimator=base, method="isotonic", cv=3)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    try:
        ll = log_loss(y_test, model.predict_proba(X_test))
    except Exception:
        ll = None

    joblib.dump(model, model_path)
    meta = {
        "feature_columns": feature_cols,
        "label_mapping": {"aws": 0, "azure": 1, "gcp": 2},
        "reverse_mapping": {0: "aws", 1: "azure", 2: "gcp"},
        "accuracy": acc,
        "log_loss": ll,
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved {model_path.name} (acc={acc:.3f}{', logloss='+str(round(ll,3)) if ll is not None else ''})")


def run():
    Path("models").mkdir(exist_ok=True)

    compute_df = gen_compute_samples(50000)
    compute_df = _encode_categoricals(compute_df, ["region", "cost_sensitivity", "instance_family"])
    _train_and_save(
        compute_df,
        label="best_provider",
        model_path=Path("models/compute_recommender.pkl"),
        meta_path=Path("models/compute_metadata.json"),
    )

    storage_df = gen_storage_samples(50000)
    storage_df = _encode_categoricals(storage_df, ["region", "cost_sensitivity"])
    _train_and_save(
        storage_df,
        label="best_provider",
        model_path=Path("models/storage_recommender.pkl"),
        meta_path=Path("models/storage_metadata.json"),
    )

    db_df = gen_database_samples(50000)
    db_df = _encode_categoricals(db_df, ["region", "cost_sensitivity"])
    _train_and_save(
        db_df,
        label="best_provider",
        model_path=Path("models/database_recommender.pkl"),
        meta_path=Path("models/database_metadata.json"),
    )


if __name__ == "__main__":
    run()
