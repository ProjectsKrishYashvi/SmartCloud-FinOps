import argparse
import json
from rules import SelectorInput, choose_cloud

def main():
    parser = argparse.ArgumentParser(description="Smart Cloud Selector")
    parser.add_argument("--region", required=True)
    parser.add_argument("--app_type", default="api")
    parser.add_argument("--cost", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--prices", required=True, help='JSON like {"aws":50,"azure":55,"gcp":60}')
    parser.add_argument("--load", default="{}", help='JSON like {"aws":0.3,"azure":0.5,"gcp":0.2}')
    args = parser.parse_args()

    prices = json.loads(args.prices)
    load = json.loads(args.load)
    sel_input = SelectorInput(
        region=args.region,
        app_type=args.app_type,
        cost_sensitive=args.cost,
        load_state=load,
        estimated_prices=prices,
    )
    provider, reason = choose_cloud(sel_input)
    print(json.dumps({"provider": provider, "reason": reason}))

if __name__ == "__main__":
    main() 