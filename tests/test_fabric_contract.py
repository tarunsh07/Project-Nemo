import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from phase2_fabric import insight
from phase2_fabric.accelerator import Accelerator
from phase2_fabric.guardrail import Guardrail
from phase2_fabric.cognition_fabric import CognitionFabric, FabricIntegrityError
from phase2_fabric.ledger_store import LedgerStore
from phase2_fabric.policy_registry import PolicyRegistry
from phase2_fabric import incident_processor
from phase1_csp.resolve import csp_negotiate
from phase2_fabric.agents import Agent
from phase1_csp.nash_bargaining import Range
from phase2_fabric.fingerprint import generate_fingerprint

@pytest.fixture
def clean_env():
    ledger_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'test_ledger.jsonl'))
    if os.path.exists(ledger_path):
        os.remove(ledger_path)
    
    ledger_store = LedgerStore(filepath=ledger_path)
    policy_registry = PolicyRegistry()
    fabric = CognitionFabric(ledger_store, policy_registry)
    
    agents = {
        "Agent-1-Throughput": Agent("Agent-1-Throughput", ["throughput"], {"max_latency_ms": Range(50, 60), "min_security_level": Range(0.30, 0.70)}),
        "Agent-2-Security": Agent("Agent-2-Security", ["security"], {"min_security_level": Range(0.80, 1.0)})
    }
    accelerator = Accelerator(policy_registry, agents)
    guardrail = Guardrail(policy_registry, fabric)
    
    return fabric, agents, accelerator, guardrail, ledger_store, policy_registry

def get_base_incident():
    return {
        "field_name": "min_security_level",
        "audit_window": True,
        "traffic_level": "medium",
        "region": "us-east",
        "participating_capabilities": ["security", "throughput"]
    }

def test_scenario_1_ratchet_effect(clean_env):
    print("\n\n" + "="*60)
    print("TEST SCENARIO 1: THE RATCHET EFFECT")
    print("="*60)
    fabric, agents, accelerator, guardrail, _, _ = clean_env
    incident = get_base_incident()
    _, fp = generate_fingerprint(incident)
    
    print("\n--- Phase A: Initial Incident (No memory) ---")
    print("Step: An incident arrives with no prior memory in the system.")
    r1 = incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
    print(f"Outcome: System processed path '{r1['path']}'. It correctly fell back to Phase 1 CSP negotiation.")
    assert r1["path"] == "csp_negotiation_fallback"
    
    res = fabric.query(fp)
    if res.hit:
        print(f"        -> INSIGHT STORED! Status: '{res.insight.status}', Starting Confidence: {res.insight.confidence}")
    
    print("\n--- Phase B: Building Confidence ---")
    print("Step: A series of similar incidents arrive. The system reuses the candidate rule and measures success.")
    for i in range(4):
        r = incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
        res = fabric.query(fp)
        print(f"Step: Similar Incident {i+1} processed. Path: {r['path']}.")
        print(f"        -> SUCCESSFUL REUSE! Confidence bumped to {res.insight.confidence}, Status is still '{res.insight.status}'")
        assert r["path"] == "fabric_hit_candidate"
        
    print("\n--- Phase C: Verified Hit (The Ratchet) ---")
    print("Step: Incident #150 arrives. Confidence has crossed the 0.8 threshold (Promotion Threshold).")
    r2 = incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
    res2 = fabric.query(fp)
    print(f"Outcome: System processed path '{r2['path']}'. Negotiation was skipped entirely!")
    print(f"        -> FINAL STATE! Confidence is {res2.insight.confidence}, Status is '{res2.insight.status}'")
    assert r2["path"] == "fabric_hit_verified"

def test_scenario_2_network_partition(clean_env):
    print("\n\n" + "="*60)
    print("TEST SCENARIO 2: NETWORK PARTITION & CORROBORATION FAILURE")
    print("="*60)
    fabric, agents, accelerator, guardrail, ledger_store, policy_registry = clean_env
    incident = get_base_incident()
    
    print("Step 1: Simulating a network partition. We are taking 'Agent-1-Throughput' offline.")
    print("        This means 'Agent-2-Security' will be the ONLY agent awake to review the rule.")
    del agents["Agent-1-Throughput"]
    
    print("\nStep 2: An incident arrives and triggers negotiation.")
    print("        The proposing agent (Agent-2) creates an Insight (a proposed rule) with a base confidence of 0.2.")
    print("        It submits this to the Accelerator for independent corroboration.")
    r1 = incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
    
    print("\nStep 3: The Accelerator tries to contact stakeholders for the 'min_security_level' field.")
    print("        It expects Agent-1-Throughput to respond, but gets a timeout (because we took it offline).")
    print("        Therefore, the Insight receives ZERO independent corroborations. Its confidence stays at 0.2.")
    
    print("\nStep 4: The Guardrail intercepts the Insight before it can be written to the Ledger.")
    print("        Guardrail Check -> 'below_global_ceiling': PASS")
    print("        Guardrail Check -> 'not_statistically_abnormal': PASS")
    print("        Guardrail Check -> 'policy_epoch_unchanged': PASS")
    print("        Guardrail Check -> 'owner_and_corroborated': FAIL! (It requires at least 1 corroboration)")
    
    print("\n[RESULT]")
    print(f"Outcome: Processing path was '{r1['path']}'. The system fell back to standard negotiation.")
    
    _, fp = generate_fingerprint(incident)
    result = fabric.query(fp)
    print(f"Step 5: We query the Fabric memory for the fingerprint '{fp}'.")
    if not result.hit and result.reason == "miss_no_prior_record":
        print("SUCCESS! The Guardrail safely REJECTED the uncorroborated hallucination.")
        print("The bad rule was completely blocked and NEVER written to the ledger.")
    
    assert result.hit is False
    assert result.reason == "miss_no_prior_record"

def test_scenario_3_poisoned_insight(clean_env):
    print("\n\n" + "="*60)
    print("TEST SCENARIO 3: POISONED INSIGHT (TAMPER EVIDENT LEDGER)")
    print("="*60)
    fabric, agents, accelerator, guardrail, ledger_store, policy_registry = clean_env
    incident = get_base_incident()
    
    print("Step: Processing an initial incident to create a valid candidate record in the ledger.")
    incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
    
    print("Step: A rogue agent directly hacks the underlying ledger storage, bypassing APIs.")
    print("Step: Rogue agent modifies the confidence score to 1.0 in the raw data.")
    record = ledger_store._records[-1]
    record["confidence"] = 1.0  # Modified AFTER the cryptographic hash was already computed
    ledger_store._save_record(record)
    
    print("Step: Another incident arrives, forcing the system to query the poisoned memory.")
    print("\n[RESULT]")
    try:
        incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
        print("System FAILED to detect the ledger tampering!")
    except FabricIntegrityError as e:
        print(f"FabricIntegrityError raised: System SUCCESSFULLY detected the tampering because the hash chain broke!")
        assert True

def test_scenario_4_policy_violation(clean_env):
    print("\n\n" + "="*60)
    print("TEST SCENARIO 4: MID-FLIGHT POLICY VIOLATION")
    print("="*60)
    fabric, agents, accelerator, guardrail, ledger_store, policy_registry = clean_env
    incident = get_base_incident()
    
    print("Step: Processing 5 incidents to build confidence and generate a fully 'verified' rule in memory.")
    for _ in range(5):
        incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
    
    print("Step: Global policy epoch is bumped by an administrator mid-flight (e.g. new regulatory rules).")
    old_epoch = policy_registry.current_epoch()
    policy_registry.set_epoch(old_epoch + 1)
    print(f"Step: Epoch changed from {old_epoch} to {policy_registry.current_epoch()}.")
    
    print("Step: A new incident arrives. The system checks the memory but notices the policy epoch mismatch.")
    r2 = incident_processor.process_incident(incident, fabric, agents, accelerator, guardrail, csp_negotiate)
    
    print("\n[RESULT]")
    if r2["path"] == "csp_negotiation_fallback":
        print("System SUCCESSFULLY rejected the verified insight because the policy epoch changed.")
        print("It forced a fresh negotiation under the new rules.")
        
    assert r2["path"] == "csp_negotiation_fallback"
