class PolicyRegistry:
    def __init__(self):
        self._epoch = 1
        self._ceilings = {
            "min_security_level": 1.0,
            "max_latency_ms": 200.0
        }
        self._owners = {
            "min_security_level": "Agent-2-Security",
            "max_latency_ms": "Agent-1-Throughput"
        }
        self._stakeholders = {
            "min_security_level": ["Agent-1-Throughput", "Agent-2-Security", "Agent-3-SLA"],
            "max_latency_ms": ["Agent-1-Throughput", "Agent-3-SLA"]
        }
        self._proposal_epochs = {}

    def current_epoch(self) -> int:
        return self._epoch
        
    def set_epoch(self, epoch: int):
        self._epoch = epoch

    def global_ceiling(self, field: str) -> float:
        return self._ceilings.get(field, float('inf'))

    def owner_of(self, field: str) -> str:
        return self._owners.get(field)

    def stakeholders_for(self, field: str) -> list[str]:
        return self._stakeholders.get(field, [])

    def record_proposal_epoch(self, insight):
        self._proposal_epochs[insight.insight_id] = self._epoch

    def epoch_at_proposal_time(self, insight) -> int:
        return self._proposal_epochs.get(insight.insight_id, self._epoch)
