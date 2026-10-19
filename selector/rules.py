from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class SelectorInput:
    region: str
    app_type: str
    cost_sensitive: str  # low | medium | high
    load_state: Dict[str, float]  # provider -> relative load (0..1)
    estimated_prices: Dict[str, float]  # provider -> price estimate


def choose_cloud(data: SelectorInput) -> Tuple[str, str]:
    prices = data.estimated_prices
    load = data.load_state or {"aws": 0.0, "azure": 0.0, "gcp": 0.0}
    normalized_region = (data.region or "").lower()

    candidates = [p for p in ["aws", "azure", "gcp"] if p in prices]
    if not candidates:
        return "aws", "Defaulted to AWS (no price data)."

    if data.cost_sensitive.lower() == "high":
        min_price = min(prices[p] for p in candidates)
        cheapest = [p for p in candidates if prices[p] == min_price]
        if len(cheapest) == 1:
            provider = cheapest[0]
            return provider, f"Chose {provider}: lowest price ({min_price})."
        # Tie-break by lower load
        provider = sorted(cheapest, key=lambda p: load.get(p, 0.0))[0]
        return provider, f"Chose {provider}: tie on price; lower current load."

    # Medium/low cost sensitivity: prefer region familiarity and balanced load
    # Simple heuristic: prefer AWS for us/eu, Azure for europe/uk, GCP for apac
    if "apac" in normalized_region or "asia" in normalized_region:
        preferred = "gcp"
    elif "eu" in normalized_region or "europe" in normalized_region or "uk" in normalized_region:
        preferred = "azure"
    else:
        preferred = "aws"

    if preferred in candidates:
        return preferred, f"Chose {preferred}: regional preference heuristic."

    # Fallback by lowest load
    provider = sorted(candidates, key=lambda p: (load.get(p, 0.0), prices.get(p, 1e9)))[0]
    return provider, f"Chose {provider}: lowest load fallback." 