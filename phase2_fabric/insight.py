from dataclasses import dataclass, field
import hashlib, json, uuid

@dataclass
class Insight:
    insight_id: str
    fingerprint: str
    rule: dict
    proposing_agent: str
    evidence_commitment_hash: str
    confidence: float = 0.2
    status: str = "proposed"  # proposed -> candidate -> verified | quarantined | rejected
    corroborations: list = field(default_factory=list)
    reuse_success_count: int = 0
    reuse_failure_count: int = 0

def hash_evidence(evidence_payload: dict) -> str:
    """Confidential logs never leave the proposing agent. Only this hash does."""
    payload = json.dumps(evidence_payload, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()

def extract_insight(fingerprint: str, failed_field: str, failed_value: float,
                     corrected_value: float, condition: dict,
                     proposing_agent: str, private_evidence: dict,
                     transfer_bonus: float = 0.0) -> Insight:
    return Insight(
        insight_id=str(uuid.uuid4()),
        fingerprint=fingerprint,
        rule={"condition": condition, "field": failed_field, "value": corrected_value},
        proposing_agent=proposing_agent,
        evidence_commitment_hash=hash_evidence(private_evidence),
        confidence=0.2 + transfer_bonus
    )
