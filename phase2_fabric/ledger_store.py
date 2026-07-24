import json
import os
from .insight import Insight

class LedgerStore:
    def __init__(self, filepath="data/fabric_ledger.jsonl"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self._records = []
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            return
        with open(self.filepath, "r") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    insight_data = rec["insight"]
                    rec["insight"] = Insight(**insight_data)
                    self._records.append(rec)

    def _save_record(self, record):
        rec_copy = dict(record)
        rec_copy["insight"] = record["insight"].__dict__
        with open(self.filepath, "a") as f:  # append-only — never overwrite
            f.write(json.dumps(rec_copy) + "\n")

    def latest(self, fingerprint: str):
        chain = self.full_chain(fingerprint)
        if chain:
            return chain[-1]
        return None

    def chain_head(self, fingerprint: str) -> str:
        latest = self.latest(fingerprint)
        return latest["chain_hash"] if latest else ""

    def full_chain(self, fingerprint: str) -> list:
        return [r for r in self._records if r["fingerprint"] == fingerprint]

    def append(self, record: dict):
        self._records.append(record)
        self._save_record(record)

    def accepted_values_for(self, field: str) -> list[float]:
        values = []
        for r in self._records:
            if r["insight"].rule["field"] == field and r["status"] in ["candidate", "verified"]:
                values.append(r["insight"].rule["value"])
        return values
