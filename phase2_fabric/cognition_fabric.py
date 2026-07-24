import hashlib, json, time
from .guardrail import PROMOTION_THRESHOLD, QUARANTINE_THRESHOLD

class FabricResult:
    def __init__(self, hit, insight=None, status=None, reason=None):
        self.hit = hit
        self.insight = insight
        self.status = status
        self.reason = reason

class CognitionFabric:
    def __init__(self, ledger_store, policy_registry):
        self.ledger_store = ledger_store
        self.policy_registry = policy_registry

    def query(self, fingerprint: str) -> FabricResult:
        record = self.ledger_store.latest(fingerprint)
        if record is None:
            return FabricResult(hit=False, reason="miss_no_prior_record")

        if not self._chain_intact(fingerprint):
            raise FabricIntegrityError(f"chain hash mismatch for {fingerprint}")

        if record["policy_epoch"] != self.policy_registry.current_epoch():
            return FabricResult(hit=False, reason="stale_policy_epoch")

        if record["status"] == "quarantined" or record["status"] == "rejected":
            return FabricResult(hit=False, reason=f"insight_{record['status']}")

        return FabricResult(hit=True, insight=record["insight"], status=record["status"])

    def store(self, insight):
        prev_hash = self.ledger_store.chain_head(insight.fingerprint)
        record = {
            "fingerprint": insight.fingerprint,
            "insight": insight,
            "status": insight.status,
            "confidence": insight.confidence,
            "evidence_commitment_hash": insight.evidence_commitment_hash,
            "policy_epoch": self.policy_registry.current_epoch(),
            "prev_chain_hash": prev_hash,
            "timestamp": time.time(),
        }
        record["chain_hash"] = self._compute_chain_hash(prev_hash, record)
        self.ledger_store.append(record)

    def record_reuse_outcome(self, fingerprint: str, success: bool):
        record = self.ledger_store.latest(fingerprint)
        insight = record["insight"]
        if success:
            insight.reuse_success_count += 1
            insight.confidence = round(min(1.0, insight.confidence + 0.075), 3)
        else:
            insight.reuse_failure_count += 1
            insight.confidence = round(max(0.0, insight.confidence - 0.15), 3)
            if insight.confidence < QUARANTINE_THRESHOLD:
                insight.status = "quarantined"
        if insight.status == "candidate" and insight.confidence >= PROMOTION_THRESHOLD:
            insight.status = "verified"
        self.store(insight)

    def value_history(self, field: str) -> list[float]:
        return self.ledger_store.accepted_values_for(field)

    def _compute_chain_hash(self, prev_hash: str, record: dict) -> str:
        payload = json.dumps({
            "fingerprint": record["fingerprint"],
            "status": record["status"],
            "confidence": record["confidence"],
            "evidence_commitment_hash": record["evidence_commitment_hash"],
            "prev_chain_hash": prev_hash,
        }, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()

    def _chain_intact(self, fingerprint: str) -> bool:
        chain = self.ledger_store.full_chain(fingerprint)
        prev = None
        for rec in chain:
            expected = self._compute_chain_hash(prev or "", rec)
            if expected != rec["chain_hash"]:
                return False
            prev = rec["chain_hash"]
        return True

class FabricIntegrityError(Exception):
    pass
