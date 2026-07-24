PROMOTION_THRESHOLD  = 0.8
QUARANTINE_THRESHOLD = 0.1

class GuardrailResult:
    def __init__(self, passed: bool, checks: dict):
        self.passed = passed
        self.checks = checks

class Guardrail:
    def __init__(self, policy_registry, fabric):
        self.policy_registry = policy_registry
        self.fabric = fabric

    def review(self, insight) -> GuardrailResult:
        checks = {
            "below_global_ceiling":   self._check_ceiling(insight),
            "owner_and_corroborated": self._check_ownership(insight),
            "not_statistically_abnormal": self._check_statistics(insight),
            "policy_epoch_unchanged": self._check_epoch(insight),
        }
        if not all(checks.values()):
            insight.status = "rejected"
            return GuardrailResult(False, checks)

        insight.status = "verified" if insight.confidence >= PROMOTION_THRESHOLD else "candidate"
        self.fabric.store(insight)
        return GuardrailResult(True, checks)

    def _check_ceiling(self, insight):
        ceiling = self.policy_registry.global_ceiling(insight.rule["field"])
        return insight.rule["value"] <= ceiling

    def _check_ownership(self, insight):
        owner = self.policy_registry.owner_of(insight.rule["field"])
        proposed_by_owner = insight.proposing_agent == owner
        corroborated = any(c["corroborates"] for c in insight.corroborations)
        return proposed_by_owner and corroborated

    def _check_statistics(self, insight):
        history = self.fabric.value_history(insight.rule["field"])
        if len(history) < 3:
            return True  # not enough history yet
        mean = sum(history) / len(history)
        variance = sum((v - mean) ** 2 for v in history) / len(history)
        stdev = variance ** 0.5 or 1e-9
        z = abs(insight.rule["value"] - mean) / stdev
        return z <= 3.0  # three-sigma gate

    def _check_epoch(self, insight):
        return self.policy_registry.current_epoch() == self.policy_registry.epoch_at_proposal_time(insight)
