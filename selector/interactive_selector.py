import json
import argparse
from rules import SelectorInput, choose_cloud

def get_user_requirements():
    print("🤖 SmartCloud FinOps - Cloud Selection Assistant")
    print("=" * 50)
    
    # App Type Selection
    print("\n📋 What type of application are you deploying?")
    print("1. Web Application (static website)")
    print("2. API/Backend Service")
    print("3. Database Server")
    print("4. Machine Learning Workload")
    print("5. High-Performance Computing")
    
    app_choices = {
        "1": "web-app",
        "2": "api-service", 
        "3": "database",
        "4": "ml-workload",
        "5": "hpc"
    }
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in app_choices:
            app_type = app_choices[choice]
            break
        print("❌ Invalid choice. Please enter 1-5.")
    
    # Region Selection
    print("\n🌍 Which region do you prefer?")
    print("1. US East (N. Virginia) - us-east-1")
    print("2. US West (Oregon) - us-west-2") 
    print("3. Europe (Ireland) - eu-west-1")
    print("4. Asia Pacific (Mumbai) - ap-south-1")
    print("5. Asia Pacific (Singapore) - ap-southeast-1")
    
    region_choices = {
        "1": "us-east-1",
        "2": "us-west-2",
        "3": "eu-west-1", 
        "4": "ap-south-1",
        "5": "ap-southeast-1"
    }
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in region_choices:
            region = region_choices[choice]
            break
        print("❌ Invalid choice. Please enter 1-5.")
    
    # Cost Sensitivity
    print("\n💰 How cost-sensitive is this deployment?")
    print("1. High - Choose the absolute cheapest option")
    print("2. Medium - Balance cost with performance")
    print("3. Low - Performance and features over cost")
    
    cost_choices = {
        "1": "high",
        "2": "medium", 
        "3": "low"
    }
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice in cost_choices:
            cost_sensitive = cost_choices[choice]
            break
        print("❌ Invalid choice. Please enter 1-3.")
    
    # Workload Size
    print("\n📊 What's your expected workload size?")
    print("1. Small - < 100 users, basic traffic")
    print("2. Medium - 100-1000 users, moderate traffic") 
    print("3. Large - 1000+ users, high traffic")
    
    size_choices = {
        "1": "small",
        "2": "medium",
        "3": "large"
    }
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice in size_choices:
            workload_size = size_choices[choice]
            break
        print("❌ Invalid choice. Please enter 1-3.")
    
    return app_type, region, cost_sensitive, workload_size

def calculate_prices(app_type, region, workload_size):
    """Calculate estimated monthly costs for each provider"""
    
    # Base prices (simplified - in real world, these would come from APIs)
    base_prices = {
        "web-app": {"aws": 25, "azure": 30, "gcp": 28},
        "api-service": {"aws": 50, "azure": 55, "gcp": 45},
        "database": {"aws": 120, "azure": 110, "gcp": 105},
        "ml-workload": {"aws": 200, "azure": 180, "gcp": 190},
        "hpc": {"aws": 300, "azure": 280, "gcp": 275}
    }
    
    # Regional adjustments
    regional_multipliers = {
        "us-east-1": 1.0,
        "us-west-2": 1.1,
        "eu-west-1": 1.2,
        "ap-south-1": 0.9,
        "ap-southeast-1": 1.0
    }
    
    # Size multipliers
    size_multipliers = {
        "small": 1.0,
        "medium": 2.5,
        "large": 5.0
    }
    
    base = base_prices[app_type]
    regional_mult = regional_multipliers[region]
    size_mult = size_multipliers[workload_size]
    
    prices = {}
    for provider, base_price in base.items():
        prices[provider] = round(base_price * regional_mult * size_mult, 2)
    
    return prices

def generate_recommendation(provider, reason, prices, app_type, region):
    """Generate a detailed recommendation"""
    
    provider_names = {
        "aws": "Amazon Web Services (AWS)",
        "azure": "Microsoft Azure", 
        "gcp": "Google Cloud Platform (GCP)"
    }
    
    print(f"\n🎯 RECOMMENDATION")
    print("=" * 30)
    print(f"✅ Recommended Provider: {provider_names[provider]}")
    print(f"💡 Reason: {reason}")
    print(f"💰 Estimated Monthly Cost: ${prices[provider]}")
    
    print(f"\n📊 Cost Comparison:")
    for p, price in prices.items():
        if p == provider:
            print(f"  ✅ {provider_names[p]}: ${price} (RECOMMENDED)")
        else:
            savings = price - prices[provider]
            print(f"  📈 {provider_names[p]}: ${price} (+${savings} more)")
    
    print(f"\n🚀 Next Steps:")
    print(f"  1. Deploy to {provider_names[provider]} using Terraform")
    print(f"  2. Monitor costs for 30 days")
    print(f"  3. Re-evaluate if requirements change")
    
    return provider, prices[provider]

def main():
    print("🚀 Starting SmartCloud FinOps Cloud Selector...")
    
    # Get user requirements
    app_type, region, cost_sensitive, workload_size = get_user_requirements()
    
    # Calculate prices
    prices = calculate_prices(app_type, region, workload_size)
    
    # Simulate current load (in real world, this would come from monitoring)
    load_state = {"aws": 0.3, "azure": 0.5, "gcp": 0.2}
    
    # Make selection
    sel_input = SelectorInput(
        region=region,
        app_type=app_type,
        cost_sensitive=cost_sensitive,
        load_state=load_state,
        estimated_prices=prices
    )
    
    provider, reason = choose_cloud(sel_input)
    
    # Generate detailed recommendation
    final_provider, final_cost = generate_recommendation(provider, reason, prices, app_type, region)
    
    # Return for automation
    return {
        "provider": final_provider,
        "cost": final_cost,
        "region": region,
        "app_type": app_type
    }

if __name__ == "__main__":
    result = main()
    print(f"\n🤖 Selection complete! Ready to deploy to {result['provider'].upper()}.")
