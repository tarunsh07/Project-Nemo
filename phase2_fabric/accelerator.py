CORROBORATION_BOOST = 0.3
DISPUTE_PENALTY      = 0.3

class Accelerator:
    def __init__(self, policy_registry, agent_registry):
        self.policy_registry = policy_registry
        self.agent_registry = agent_registry

    def submit(self, insight):
        stakeholders = self.policy_registry.stakeholders_for(insight.rule["field"])
        reviewers = [a for a in stakeholders if a != insight.proposing_agent]

        for agent_id in reviewers:
            agent = self.agent_registry.get(agent_id)
            if not agent:
                continue

            verdict = agent.verify_insight(insight)
            insight.corroborations.append({
                "agent": agent_id, "corroborates": verdict.corroborates,
                "reasoning": verdict.reasoning,
            })
            delta = CORROBORATION_BOOST if verdict.corroborates else -DISPUTE_PENALTY
            insight.confidence = min(1.0, max(0.0, insight.confidence + delta))

        return insight
