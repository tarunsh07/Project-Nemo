from dataclasses import dataclass

@dataclass
class Range:
    lo: float
    hi: float

@dataclass
class Resolution:
    value: float
    method: str  # "nash_bargain" | "policy_floor"

def resolve_contested_field(range_a: Range, range_b: Range,
                             weight_a: float, weight_b: float,
                             policy_floor: float) -> Resolution:
    lo = max(range_a.lo, range_b.lo)
    hi = min(range_a.hi, range_b.hi)

    if lo <= hi:
        x_star = (weight_a * lo + weight_b * hi) / (weight_a + weight_b)
        return Resolution(value=round(x_star, 2), method="nash_bargain")

    return Resolution(value=policy_floor, method="policy_floor")


def derive_priority_weight(agent_stakes: float, all_stakes: list[float]) -> float:
    return agent_stakes / sum(all_stakes)
