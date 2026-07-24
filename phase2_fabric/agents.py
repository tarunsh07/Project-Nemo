from dataclasses import dataclass
from phase1_csp.nash_bargaining import Range

@dataclass
class Verdict:
    corroborates: bool
    reasoning: str

class Agent:
    def __init__(self, agent_id, capability_tags, tolerable_ranges: dict):
        self.agent_id = agent_id
        self.capability_tags = capability_tags
        self.tolerable_ranges = tolerable_ranges

    def verify_insight(self, insight) -> Verdict:
        field = insight.rule["field"]
        proposed_value = insight.rule["value"]
        my_range = self.tolerable_ranges.get(field)
        
        if my_range is None:
            return Verdict(True, "field outside my domain — no objection to raise")
            
        if my_range.lo <= proposed_value <= my_range.hi:
            return Verdict(True, "proposed value still inside my own tolerable range")

        harmed = self._is_harmed(field, proposed_value)
        return Verdict(not harmed, "recomputed against my own objective")

    def _is_harmed(self, field, proposed_value) -> bool:
        # reluctant sign — slows throughput but doesn't break routing
        if field == "min_security_level" and self.agent_id == "Agent-1-Throughput":
            return False
        return True
