import json
import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from datetime import datetime

class ServiceModelRegistry:
    def __init__(self):
        self.models = {}
        self.metas = {}
        self._load()

    def _load(self):
        def load_pair(name: str):
            model_path = Path(f"models/{name}_recommender.pkl")
            meta_path = Path(f"models/{name}_metadata.json")
            if model_path.exists() and meta_path.exists():
                self.models[name] = joblib.load(model_path)
                with meta_path.open("r", encoding="utf-8") as f:
                    self.metas[name] = json.load(f)
        for svc in ["compute", "storage", "database"]:
            load_pair(svc)

    def predict(self, service: str, features: Dict[str, float]) -> Tuple[str, float]:
        name = service
        model = self.models.get(name)
        meta = self.metas.get(name)
        if not model or not meta:
            return "aws", 0.0
        feature_vec = [0.0] * len(meta["feature_columns"])
        fmap = {c: i for i, c in enumerate(meta["feature_columns"])}
        # Fill vector
        for k, v in features.items():
            if k in fmap:
                feature_vec[fmap[k]] = v
        pred = model.predict([feature_vec])[0]
        conf = float(max(model.predict_proba([feature_vec])[0]))
        provider = meta["reverse_mapping"][str(pred)] if isinstance(meta["reverse_mapping"], dict) else meta["reverse_mapping"][pred]
        return provider, conf

class HybridRecommender:
    def __init__(self, model_path: str = "models/recommender.pkl"):
        self.model_path = model_path
        self.model = None
        self.metadata = None
        self.service_registry = ServiceModelRegistry()
        self.load_model()
    
    def load_model(self):
        try:
            self.model = joblib.load(self.model_path)
            with open("models/metadata.json", "r") as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            self.model = None
            self.metadata = None
    
    def rule_based_decision(self, service: str, service_costs: Dict[str, float], 
                           region: str = "us-east-1", cost_sensitivity: str = "medium") -> Tuple[str, str]:
        if not service_costs or len(service_costs) < 1:
            return "aws", "Default fallback"
        best_provider = min(service_costs.items(), key=lambda x: x[1])[0]
        regional_preferences = {"us-east-1": "aws", "us-west-2": "aws", "eu-west-1": "azure", "ap-south-1": "gcp", "ap-southeast-1": "gcp"}
        preferred = regional_preferences.get(region, best_provider)
        if cost_sensitivity == "high":
            return best_provider, f"Cost-optimized: {best_provider.upper()} is cheapest"
        if cost_sensitivity == "low" and preferred in service_costs:
            return preferred, f"Performance-optimized: {preferred.upper()} preferred for region"
        return best_provider, f"Balanced: {best_provider.upper()} is cheapest"

    def ml_prediction(self, service: str, feature_row: Dict[str, float]) -> Tuple[str, float, str]:
        provider, conf = self.service_registry.predict(service, feature_row)
        return provider, conf, f"ML ({service}) suggests {provider.upper()} (confidence {conf:.2f})"

    def hybrid_decision(self, service: str, service_costs: Dict[str, float], feature_row: Dict[str, float],
                        region: str = "us-east-1", cost_sensitivity: str = "medium") -> Dict:
        rule_provider, rule_reason = self.rule_based_decision(service, service_costs, region, cost_sensitivity)
        ml_provider, ml_conf, ml_reason = self.ml_prediction(service, feature_row)
        # Compute simple cost delta rationale
        current_min = min(service_costs.values()) if service_costs else 0
        cost_delta = {p: service_costs[p] - current_min for p in service_costs}
        rationale_tail = f" Cost deltas vs cheapest: " + ", ".join([f"{p}={cost_delta[p]:+.2f}" for p in sorted(cost_delta.keys())])

        if ml_conf > 0.8:
            final_provider = ml_provider
            source = "ML (High Confidence)"
            explanation = f"ML selected {ml_provider.upper()} with confidence {ml_conf:.2f}." + rationale_tail
            confidence = ml_conf
        elif 0.6 <= ml_conf <= 0.8:
            final_provider = rule_provider
            source = "Rule-based (ML Suggested)"
            explanation = f"ML suggested {ml_provider.upper()} (confidence {ml_conf:.2f}), but rule-based decision preferred: {rule_reason}." + rationale_tail
            confidence = 1.0 - ml_conf
        else:
            final_provider = rule_provider
            source = "Rule-based (ML Low Confidence)"
            explanation = f"Rule-based decision: {rule_reason}. ML confidence too low ({ml_conf:.2f})." + rationale_tail
            confidence = 1.0 - ml_conf
        return {
            "final_provider": final_provider,
            "rule_provider": rule_provider,
            "ml_provider": ml_provider,
            "ml_confidence": ml_conf,
            "decision_source": source,
            "confidence": confidence,
            "explanation": explanation,
        }

    def generate_service_recommendation(self, service: str, service_costs: Dict[str, float], feature_row: Dict[str, float],
                                       current_provider: str) -> Dict:
        decision = self.hybrid_decision(service, service_costs, feature_row)
        current_cost = service_costs.get(current_provider, 0.0)
        suggested_cost = service_costs.get(decision["final_provider"], 0.0)
        savings = current_cost - suggested_cost
        pct = (savings / current_cost * 100) if current_cost > 0 else 0
        strength = "Strong" if pct > 20 else "Moderate" if pct > 10 else "Weak" if pct > 5 else "Minimal"
        return {
            "service": service,
            "current_provider": current_provider,
            "current_cost": current_cost,
            "suggested_provider": decision["final_provider"],
            "suggested_cost": suggested_cost,
            "savings": savings,
            "savings_percent": pct,
            "strength": strength,
            "recommendation": decision["explanation"],
            "decision_source": decision["decision_source"],
            "confidence": decision["confidence"],
            "rule_provider": decision["rule_provider"],
            "ml_provider": decision["ml_provider"],
            "ml_confidence": decision["ml_confidence"],
        }

def load_processed_data() -> Dict[str, List[Dict]]:
    """Load processed billing data grouped by tenant"""
    tenant_data = defaultdict(list)
    input_dir = Path("outputs/processed")
    
    for file in input_dir.glob("*_cleaned.csv"):
        with file.open("r", encoding="utf-8") as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                tenant_id = row.get("tenant_id", "unknown")
                tenant_data[tenant_id].append(row)
    
    return dict(tenant_data)

def calculate_service_costs(tenant_data: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Calculate cost per service per provider"""
    service_costs = defaultdict(lambda: defaultdict(float))
    
    for row in tenant_data:
        service = row.get("service", "Unknown")
        provider = row.get("provider", "Unknown")
        cost = float(row.get("cost", 0) or 0)
        service_costs[service][provider] += cost
    
    return dict(service_costs)

def load_billing_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def features_from_billing_row(row: pd.Series) -> Tuple[str, Dict[str, float], Dict[str, float], str]:
    service = row["service"].strip().lower()
    provider = row["provider"].strip().lower()
    region = row.get("region", "us-east-1")
    cost = float(row.get("cost", 0) or 0)
    unit = str(row.get("unit", "")).lower()
    usage = float(row.get("usage_amount", 0) or 0)
    cost_sensitivity = "high"  # default; could be derived from tenant policy later

    # Build per-service features and a service_costs dict using the row's provider as current cost
    feature_row: Dict[str, float] = {}
    service_costs: Dict[str, float] = {}

    if service == "compute":
        feature_row = {
            "usage_hours": usage if unit in ("hours", "hour") else usage,
            "monthly_cost": cost,
        }
    elif service == "storage":
        feature_row = {
            "storage_gb": usage if unit in ("gb", "gib") else usage,
            "requests": 0.0,
            "monthly_cost": cost,
        }
    elif service in ("database", "db"):
        feature_row = {
            "db_storage_gb": usage if unit in ("gb", "gib") else usage,
            "db_usage_hours": 720.0,
            "monthly_cost": cost,
        }
        service = "database"
    else:
        # Fallback treat as compute
        feature_row = {"usage_hours": usage, "monthly_cost": cost}
        service = "compute"

    # One-hot like region and cost_sensitivity flags if models expect them
    # We do not know exact columns; the model registry will ignore unknown features
    feature_row.update({
        f"region_{region.replace('-', '_')}": 1.0,
        f"cost_sensitivity_{cost_sensitivity}": 1.0,
    })

    # For service_costs, we only know current provider cost from billing row; others unknown
    service_costs[provider] = cost
    # Heuristic: estimate other providers as +/- 10% for demo comparison
    for p in ["aws", "azure", "gcp"]:
        if p not in service_costs:
            service_costs[p] = cost * (1 + (0.1 if p > provider else -0.1))

    return service, feature_row, service_costs, provider

def generate_tenant_recommendations(tenant_id: str, tenant_data: List[Dict], 
                                 region: str = "us-east-1", cost_sensitivity: str = "medium") -> Dict:
    """Generate hybrid recommendations for a tenant"""
    service_costs = calculate_service_costs(tenant_data)
    
    # Initialize hybrid recommender
    recommender = HybridRecommender()
    
    recommendations = []
    total_potential_savings = 0.0
    
    for service, costs in service_costs.items():
        if len(costs) < 2:
            continue
            
        # Find current provider (highest cost)
        current_provider = max(costs.items(), key=lambda x: x[1])[0]
        
        # Generate hybrid recommendation
        rec = recommender.generate_service_recommendation(
            service, costs, current_provider
        )
        
        if rec:
            recommendations.append(rec)
            if rec['savings'] > 0:
                total_potential_savings += rec['savings']
    
    # Sort by potential savings
    recommendations.sort(key=lambda x: x["savings"], reverse=True)
    
    return {
        'tenant_id': tenant_id,
        'recommendations': recommendations,
        'total_savings': total_potential_savings,
        'services_analyzed': len(recommendations),
        'services_with_savings': len([r for r in recommendations if r['savings'] > 0]),
        'generated_at': datetime.now().isoformat()
    }

def generate_tenant_recommendations_from_billing(tenant_id: str, billing_csv: Path) -> Dict:
    df = load_billing_csv(billing_csv)
    recommender = HybridRecommender()
    recs = []
    total = 0.0
    for _, row in df.iterrows():
        svc, feat, costs, current = features_from_billing_row(row)
        rec = recommender.generate_service_recommendation(svc, costs, feat, current)
        recs.append(rec)
        if rec["savings"] > 0:
            total += rec["savings"]
    recs.sort(key=lambda r: r["savings"], reverse=True)
    return {
        "tenant_id": tenant_id,
        "recommendations": recs,
        "total_savings": total,
        "services_analyzed": len(recs),
        "services_with_savings": len([r for r in recs if r["savings"] > 0]),
        "generated_at": datetime.now().isoformat(),
    }

def export_recommendations(tenant_id: str, results: Dict, output_dir: Path, show_comparison: bool = False):
    """Export recommendations in multiple formats with optional comparison data"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    header = [
        f"Hybrid Service-Level Recommendations for {tenant_id}",
        "=" * 70,
        "",
        "Summary:",
        f"   Services analyzed: {results['services_analyzed']}",
        f"   Services with savings potential: {results['services_with_savings']}",
        f"   Total potential monthly savings: ${results['total_savings']:.2f}",
        f"   Generated at: {results['generated_at']}",
        "",
        "Detailed Recommendations:",
        "",
    ]
    lines = []
    for i, rec in enumerate(results["recommendations"], 1):
        lines.extend([
            f"{i}. Service: {rec['service']}",
            f"   Current: ${rec['current_cost']:.2f} on {rec['current_provider'].upper()}",
            f"   Suggested: {rec['suggested_provider'].upper()} (${rec['suggested_cost']:.2f})",
            f"   Savings: ${rec['savings']:.2f} ({rec['savings_percent']:.1f}%)",
            f"   Strength: {rec['strength']}",
            f"   Decision Source: {rec['decision_source']}",
            f"   Confidence: {rec['confidence']:.2f}",
        ])
        if show_comparison:
            lines.extend([
                f"   Rule-based decision: {rec['rule_provider'].upper()}",
                f"   ML decision: {rec['ml_provider'].upper()} (confidence: {rec['ml_confidence']:.2f})",
                f"   Final: {rec['suggested_provider'].upper()} ({rec['decision_source']})",
            ])
        # Replace informal recommendation with professional explanation
        lines.extend([f"   Rationale: {rec['recommendation']}", ""]) 

    text_file = output_dir / f"{tenant_id}_hybrid_recommendations.txt"
    with text_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(header + lines))
    json_file = output_dir / f"{tenant_id}_hybrid_recommendations.json"
    with json_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    csv_file = None
    if results["recommendations"]:
        df = pd.DataFrame([{
            "service": r["service"],
            "current_provider": r["current_provider"],
            "current_cost": r["current_cost"],
            "suggested_provider": r["suggested_provider"],
            "suggested_cost": r["suggested_cost"],
            "savings": r["savings"],
            "savings_percent": r["savings_percent"],
            "strength": r["strength"],
            "decision_source": r["decision_source"],
            "confidence": r["confidence"],
            "rule_provider": r["rule_provider"],
            "ml_provider": r["ml_provider"],
            "ml_confidence": r["ml_confidence"],
        } for r in results["recommendations"]])
        csv_file = output_dir / f"{tenant_id}_hybrid_recommendations.csv"
        df.to_csv(csv_file, index=False)
    return text_file, json_file, csv_file

def main(tenant_id: str = None, show_comparison: bool = False):
    """Main function for hybrid recommendations"""
    print("Hybrid Recommender System")
    print("=" * 50)
    
    # Billing CSV override via env or default path
    billing_path = os.environ.get("BILLING_CSV")
    if not billing_path and tenant_id:
        candidate = Path(f"inputs/billing_{tenant_id}.csv")
        if candidate.exists():
            billing_path = str(candidate)
    if billing_path:
        tenant = tenant_id or Path(billing_path).stem.replace("billing_", "")
        print(f"Using billing CSV: {billing_path}")
        results = generate_tenant_recommendations_from_billing(tenant, Path(billing_path))
        text_file, json_file, csv_file = export_recommendations(tenant, results, Path("outputs/recommendations"), show_comparison)
        print(f"Exported: {text_file}, {json_file}, {csv_file}")
        print("\nTop recommendations:")
        for i, rec in enumerate(results['recommendations'][:3], 1):
            if show_comparison:
                print(f"  {i}. {rec['service']}: Rule={rec['rule_provider'].upper()}, ML={rec['ml_provider'].upper()} ({rec['ml_confidence']:.2f}), Final={rec['suggested_provider'].upper()} (${rec['savings']:.2f})")
            else:
                print(f"  {i}. {rec['service']}: {rec['suggested_provider'].upper()} (${rec['savings']:.2f})")
        return
    
    # Fallback to previous processed-data path if no billing CSV
    tenant_data = load_processed_data()
    tenants_to_process = [tenant_id] if tenant_id else list(tenant_data.keys())
    for t_id in tenants_to_process:
        print(f"\n📋 Processing {t_id}...")
        results = generate_tenant_recommendations(t_id, tenant_data[t_id])
        text_file, json_file, csv_file = export_recommendations(t_id, results, Path("outputs/recommendations"), show_comparison)
        print(f"✅ Exported: {text_file}, {json_file}, {csv_file}")
        print(f"\n🔝 Top 3 Recommendations for {t_id}:")
        for i, rec in enumerate(results['recommendations'][:3], 1):
            if show_comparison:
                print(f"  {i}. {rec['service']}: Rule={rec['rule_provider'].upper()}, ML={rec['ml_provider'].upper()} ({rec['ml_confidence']:.2f}), Final={rec['suggested_provider'].upper()} (${rec['savings']:.2f})")
            else:
                print(f"  {i}. {rec['service']}: {rec['suggested_provider'].upper()} (${rec['savings']:.2f})")

if __name__ == "__main__":
    import sys
    tenant = sys.argv[1] if len(sys.argv) > 1 else None
    show_compare = "--compare" in sys.argv
    main(tenant, show_compare)
