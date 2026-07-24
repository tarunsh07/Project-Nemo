from phase2_fabric.insight import Insight
from phase2_fabric.cognition_fabric import FabricIntegrityError
import json
import copy

class ChaosInjector:
    def __init__(self, fabric, accelerator, guardrail, agents, ledger_store, policy_registry):
        self.fabric = fabric
        self.accelerator = accelerator
        self.guardrail = guardrail
        self.agents = agents
        self.ledger_store = ledger_store
        self.policy_registry = policy_registry

    def inject_network_partition(self, insight: Insight):
        """
        Simulates a network partition by temporarily removing the reviewer agent
        from the agents registry before submitting to the accelerator.
        """
        print("\n[CHAOS] Injecting Network Partition: Simulating a timeout from 'Agent-1-Throughput'")
        # Temporarily remove Agent-1-Throughput to simulate partition
        agent1 = self.agents.pop("Agent-1-Throughput", None)
        
        # Submit to accelerator (Agent-1 won't respond)
        self.accelerator.submit(insight)
        
        # Restore agent
        if agent1:
            self.agents["Agent-1-Throughput"] = agent1
            
        print("[CHAOS] Network partition simulation complete. Checking guardrail response...")
        return self.guardrail.review(insight)

    def inject_poisoned_insight(self, insight: Insight):
        """
        Simulates a malicious agent trying to write a doctored record directly to the ledger,
        bypassing the guardrail and modifying the hash chain.
        """
        print("\n[CHAOS] Injecting Poisoned Insight: A rogue agent is doctoring the ledger...")
        
        # Try to use standard store to get it in the ledger (as candidate)
        self.fabric.store(insight)
        
        # Now the rogue agent hacks the underlying storage
        print("[CHAOS] Rogue agent manually modifying confidence to 1.0 in the raw ledger...")
        record = self.ledger_store._records[-1]
        record["confidence"] = 1.0  # Modified after hash was computed!
        self.ledger_store._save_record(record)
        
        print("[CHAOS] Poisoned update injected. Checking fabric response on next query...")

    def inject_policy_violation(self, fingerprint: str):
        """
        Simulates a mid-flight policy change (e.g. regulatory update) and ensures
        that older verified insights are invalidated.
        """
        print("\n[CHAOS] Injecting Policy Violation: Global policy epoch is being bumped mid-flight!")
        old_epoch = self.policy_registry.current_epoch()
        self.policy_registry.set_epoch(old_epoch + 1)
        
        print(f"[CHAOS] Epoch changed from {old_epoch} to {self.policy_registry.current_epoch()}.")
        print("[CHAOS] Policy violation injected. Attempting to query stale insight...")
        return self.fabric.query(fingerprint)
