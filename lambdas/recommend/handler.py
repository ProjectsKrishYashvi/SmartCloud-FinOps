import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

INPUT_DIR = Path(os.environ.get("INPUT_DIR", "outputs/processed"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "outputs/recommendations"))


def load_processed_data() -> Dict[str, List[Dict]]:
    """Load processed billing data grouped by tenant"""
    tenant_data = defaultdict(list)
    
    for file in INPUT_DIR.glob("*_cleaned.csv"):
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


def find_best_provider(service_costs: Dict[str, float]) -> Tuple[str, float]:
    """Find the cheapest provider for a service"""
    if not service_costs:
        return "Unknown", 0.0
    
    best_provider = min(service_costs.items(), key=lambda x: x[1])
    return best_provider[0], best_provider[1]


def generate_service_recommendation(service: str, service_costs: Dict[str, float]) -> Dict:
    """Generate recommendation for a specific service"""
    if len(service_costs) < 2:
        return None  # Need at least 2 providers to compare
    
    # Find current provider (highest cost) and best provider (lowest cost)
    current_provider = max(service_costs.items(), key=lambda x: x[1])
    best_provider, best_cost = find_best_provider(service_costs)
    
    current_cost = current_provider[1]
    savings = current_cost - best_cost
    savings_percent = (savings / current_cost * 100) if current_cost > 0 else 0
    
    # Determine recommendation strength
    if savings_percent > 20:
        recommendation = f"Strong recommendation: Migrate {service} to {best_provider.upper()} for {savings_percent:.1f}% savings (${savings:.2f}/month)."
    elif savings_percent > 10:
        recommendation = f"Consider migrating {service} to {best_provider.upper()} for {savings_percent:.1f}% savings (${savings:.2f}/month)."
    elif savings_percent > 5:
        recommendation = f"Small savings possible: {service} could save {savings_percent:.1f}% (${savings:.2f}/month) on {best_provider.upper()}, but migration effort may not be worth it."
    else:
        recommendation = f"Minimal savings: {service} shows only {savings_percent:.1f}% potential savings. Current provider is optimal."
    
    return {
        "service": service,
        "current_provider": current_provider[0],
        "current_cost": current_cost,
        "suggested_provider": best_provider,
        "suggested_cost": best_cost,
        "savings": savings,
        "savings_percent": savings_percent,
        "recommendation": recommendation
    }


def generate_tenant_recommendations(tenant_id: str, tenant_data: List[Dict]) -> str:
    """Generate service-level recommendations for a tenant"""
    service_costs = calculate_service_costs(tenant_data)
    
    lines = [f"🎯 Service-Level Recommendations for {tenant_id}"]
    lines.append("=" * 60)
    lines.append("")
    
    total_potential_savings = 0.0
    recommendations = []
    
    for service, costs in service_costs.items():
        rec = generate_service_recommendation(service, costs)
        if rec:
            recommendations.append(rec)
    
    # Sort by potential savings (descending)
    recommendations.sort(key=lambda x: x["savings"], reverse=True)
    
    for rec in recommendations:
        lines.append(f"📊 Service: {rec['service']}")
        lines.append(f"   Current: ${rec['current_cost']:.2f} on {rec['current_provider'].upper()}")
        lines.append(f"   Suggested: {rec['suggested_provider'].upper()} (${rec['suggested_cost']:.2f})")
        lines.append(f"   Savings: ${rec['savings']:.2f} ({rec['savings_percent']:.1f}%)")
        lines.append(f"   💡 {rec['recommendation']}")
        lines.append("")
        
        if rec['savings'] > 0:
            total_potential_savings += rec['savings']
    
    # Summary
    lines.append("📈 SUMMARY")
    lines.append("-" * 30)
    lines.append(f"Total potential monthly savings: ${total_potential_savings:.2f}")
    lines.append(f"Services analyzed: {len(recommendations)}")
    lines.append(f"Services with savings potential: {len([r for r in recommendations if r['savings'] > 0])}")
    
    return "\n".join(lines)


def handler(event, context):
    """Main handler for service-level recommendations"""
    print("🔍 Generating service-level recommendations...")
    
    # Load processed data
    tenant_data = load_processed_data()
    
    if not tenant_data:
        print("❌ No processed data found. Run ETL first.")
        return {"status": "error", "message": "No processed data found"}
    
    summaries = {}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for tenant_id, data in tenant_data.items():
        print(f"📋 Processing {tenant_id}...")
        
        # Generate service-level recommendations
        text = generate_tenant_recommendations(tenant_id, data)
        summaries[tenant_id] = text
        
        # Write to file
        output_file = OUTPUT_DIR / f"{tenant_id}_service_recommendations.txt"
        with output_file.open("w", encoding="utf-8") as f:
            f.write(text)
        
        print(f"✅ Generated recommendations for {tenant_id}")
        print(f"📄 Saved to: {output_file}")
    
    # Print summary
    print("\n🎉 Service-level recommendations generated!")
    print(f"📊 Tenants processed: {len(summaries)}")
    
    return {
        "status": "ok", 
        "tenants": list(summaries.keys()),
        "message": f"Generated service-level recommendations for {len(summaries)} tenants"
    }


if __name__ == "__main__":
    result = handler({}, {})
    print(f"\n📋 Result: {result}") 