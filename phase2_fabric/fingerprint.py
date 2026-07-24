import hashlib, json

def canonicalize_context(incident: dict) -> str:
    canonical = {
        "field": incident["field_name"],
        "audit_window": bool(incident["audit_window"]),
        "traffic_level": incident["traffic_level"],
        "region": incident["region"],
        "capabilities": sorted(incident["participating_capabilities"]),  # sort avoids order-based misses
    }
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))

def generate_fingerprint(incident: dict) -> tuple[str, str]:
    canonical = canonicalize_context(incident)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    short = digest[:3].upper()
    return f"FP-{short}", digest
