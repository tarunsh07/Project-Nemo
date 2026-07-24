from .fingerprint import generate_fingerprint
from .insight import extract_insight

class Outcome:
    def __init__(self, success: bool, corrected_value: float = None, diagnosing_agent: str = None, evidence: dict = None):
        self.success = success
        self.corrected_value = corrected_value
        self.diagnosing_agent = diagnosing_agent
        self.evidence = evidence or {}

def apply_rule(rule):
    pass

def observe_real_world_outcome(incident, rule) -> Outcome:
    # mocked; swap with datadog/cloudwatch hook in prod
    if incident.get("audit_window") and rule["value"] == 0.75:
        return Outcome(
            success=False,
            corrected_value=0.85,
            diagnosing_agent="Agent-2-Security",
            evidence={"log": "audit failed with 0.75 floor"}
        )
    return Outcome(success=True)

def process_incident(incident, fabric, agents, accelerator, guardrail, negotiate_fn):
    display_fp, fp = generate_fingerprint(incident)
    result = fabric.query(fp)

    if result.hit and result.status == "verified":
        apply_rule(result.insight.rule)
        return {"path": "fabric_hit_verified", "fingerprint": display_fp}

    if result.hit and result.status == "candidate":
        apply_rule(result.insight.rule)
        outcome = observe_real_world_outcome(incident, result.insight.rule)
        fabric.record_reuse_outcome(fp, success=outcome.success)
        if not outcome.success:
            _raise_new_insight(incident, fp, result.insight, outcome, fabric, accelerator, guardrail)
        return {"path": "fabric_hit_candidate", "fingerprint": display_fp, "outcome": outcome.success}

    # cache miss — fall back to phase 1
    resolution = negotiate_fn(incident, agents)
    apply_rule(resolution)
    outcome = observe_real_world_outcome(incident, resolution)
    if not outcome.success:
        _raise_new_insight(incident, fp, None, outcome, fabric, accelerator, guardrail,
                            base_resolution=resolution)
    return {"path": "csp_negotiation_fallback", "fingerprint": display_fp, "outcome": outcome.success}


import itertools

def check_transfer_learning(incident, fabric):
    caps = incident["participating_capabilities"]
    if len(caps) <= 1:
        return 0.0
    
    for subset in itertools.combinations(caps, len(caps) - 1):
        test_incident = incident.copy()
        test_incident["participating_capabilities"] = list(subset)
        _, test_fp = generate_fingerprint(test_incident)
        res = fabric.query(test_fp)
        if res.hit and res.status == "verified":
            return 0.15
    return 0.0

def _raise_new_insight(incident, fp, prior_insight, outcome, fabric, accelerator, guardrail,
                        base_resolution=None):
    transfer_bonus = check_transfer_learning(incident, fabric)
    
    insight = extract_insight(
        fingerprint=fp,
        failed_field=incident["field_name"],
        failed_value=(prior_insight.rule["value"] if prior_insight else base_resolution["value"]),
        corrected_value=outcome.corrected_value,
        condition={"audit_window": incident["audit_window"]},
        proposing_agent=outcome.diagnosing_agent,
        private_evidence=outcome.evidence,
        transfer_bonus=transfer_bonus
    )
    fabric.policy_registry.record_proposal_epoch(insight)
    
    accelerator.submit(insight)
    guardrail.review(insight)
