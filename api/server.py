import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from phase2_fabric.cognition_fabric import CognitionFabric
from phase2_fabric.ledger_store import LedgerStore
from phase2_fabric.policy_registry import PolicyRegistry
from phase2_fabric.accelerator import Accelerator
from phase2_fabric.guardrail import Guardrail
from phase2_fabric import incident_processor
from phase1_csp.resolve import csp_negotiate
from phase2_fabric.agents import Agent
from phase1_csp.nash_bargaining import Range
from chaos.chaos_injector import ChaosInjector
app = FastAPI(title="Cognition Fabric API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ledger_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'fabric_ledger.jsonl'))
ledger_store = LedgerStore(filepath=ledger_path)
policy_registry = PolicyRegistry()
fabric = CognitionFabric(ledger_store, policy_registry)
def get_agents():
    return {
        "Agent-1-Throughput": Agent("Agent-1-Throughput", ["throughput"], {"max_latency_ms": Range(50, 60), "min_security_level": Range(0.30, 0.70)}),
        "Agent-2-Security": Agent("Agent-2-Security", ["security"], {"min_security_level": Range(0.80, 1.0)})
    }
global_agents = get_agents()
accelerator = Accelerator(policy_registry, global_agents)
guardrail = Guardrail(policy_registry, fabric)
chaos = ChaosInjector(fabric, accelerator, guardrail, global_agents, ledger_store, policy_registry)
class IncidentRequest(BaseModel):
    field_name: str
    audit_window: bool
    traffic_level: str
    region: str
    participating_capabilities: list[str]
@app.get("/api/ledger")
def get_ledger():
    return {"records": ledger_store._records}
@app.get("/api/agents")
def get_current_agents():
    return {"agents": list(global_agents.keys())}
@app.post("/api/incident")
def trigger_incident(req: IncidentRequest):
    try:
        incident = req.model_dump()
        result = incident_processor.process_incident(incident, fabric, global_agents, accelerator, guardrail, csp_negotiate)
        return {"status": "success", "path": result["path"], "result": result.get("result", {})}
    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.post("/api/chaos/network_partition")
def chaos_network_partition():
    global global_agents
    if "Agent-1-Throughput" in global_agents:
        del global_agents["Agent-1-Throughput"]
        return {"status": "Partition Injected: Agent-1 Offline"}
    return {"status": "Already partitioned"}
@app.post("/api/chaos/heal_network")
def chaos_heal_network():
    global global_agents
    global_agents = get_agents()
    return {"status": "Network Healed: Agent-1 Online"}
@app.post("/api/chaos/policy_violation")
def chaos_policy_violation():
    old_epoch = policy_registry.current_epoch()
    policy_registry.set_epoch(old_epoch + 1)
    return {"status": "Policy Epoch Bumped", "old_epoch": old_epoch, "new_epoch": policy_registry.current_epoch()}
@app.post("/api/agents/onboard_agent3")
def onboard_agent3():
    global global_agents
    global_agents["Agent-3-Cost"] = Agent("Agent-3-Cost", ["cost"], {"min_security_level": Range(0.75, 1.0)})
    return {"status": "Agent-3-Cost onboarded!"}
@app.post("/api/chaos/poison_ledger")
def chaos_poison_ledger():
    import json
    if len(ledger_store._records) > 0:
        ledger_store._records[-1]['confidence'] = 1.0 
        with open(ledger_store.filepath, 'w') as f:
            for r in ledger_store._records:
                f.write(json.dumps(r) + '\n')
        return {"status": "Ledger Poisoned. Integrity compromised."}
    return {"status": "Ledger empty"}
@app.post("/api/reset")
def reset_network():
    global global_agents
    global_agents = get_agents()
    ledger_store._records = []
    if os.path.exists(ledger_store.filepath):
        open(ledger_store.filepath, 'w').close()
    policy_registry._epoch = 1
    return {"status": "Network and Memory completely reset!"}

frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("api.server:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))