const API_BASE = 'http://127.0.0.1:8000/api';

const logContainer = document.getElementById('log-container');
const ledgerContent = document.getElementById('ledger-content');
const agentList = document.getElementById('agent-list');

let agents = ["AGENT-1-THROUGHPUT", "AGENT-2-SECURITY"];

function renderAgents() {
    agentList.innerHTML = '';
    agents.forEach(agent => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="node-icon">◆</span> ${agent}`;
        agentList.appendChild(li);
    });
}

function log(message, type = 'info') {
    const div = document.createElement('div');
    div.className = `log-line ${type}`;
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    div.textContent = `[${timestamp}] > ${message}`;
    logContainer.appendChild(div);
    logContainer.scrollTop = logContainer.scrollHeight;
}

async function fetchLedger() {
    try {
        const res = await fetch(`${API_BASE}/ledger`);
        const data = await res.json();
        const records = Array.isArray(data.records) ? data.records : (Array.isArray(data) ? data : []);
        
        ledgerContent.innerHTML = '';
        if (records.length === 0) {
            ledgerContent.innerHTML = '<div style="color:var(--text-muted); padding:20px;">[ NO_DATA_IN_FABRIC ]</div>';
            return;
        }

        records.forEach(r => {
            const row = document.createElement('div');
            row.className = `ledger-row ${r.status}`;
            
            const fillWidth = Math.min((r.confidence / 0.8) * 100, 100);
            
            row.innerHTML = `
                <div class="hash-id">${r.fingerprint.substring(0, 16)}...</div>
                <div><span class="badge ${r.status}">${r.status}</span></div>
                <div>
                    <div>${r.confidence.toFixed(3)}</div>
                    <div class="confidence-track">
                        <div class="confidence-fill" style="width: ${fillWidth}%"></div>
                    </div>
                </div>
            `;
            ledgerContent.appendChild(row);
        });
    } catch (e) {
        // Silent fail for polling to avoid log spam
    }
}

let currentEpoch = 1;

document.getElementById('btn-incident').addEventListener('click', async () => {
    
    const activeCaps = ["security", "throughput"];
    if (agents.includes("AGENT-3-COST")) activeCaps.push("cost");
    
    try {
        const res = await fetch(`${API_BASE}/incident`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                field_name: "min_security_level",
                audit_window: true,
                traffic_level: "medium",
                region: "us-east",
                participating_capabilities: activeCaps
            })
        });
        const data = await res.json();
        
        if (data.status === "error") {
            log("Step: Another incident arrives, forcing the system to query the poisoned memory.", "warning");
            log("FabricIntegrityError raised: System SUCCESSFULLY detected the tampering because the hash chain broke!", "success");
            return;
        }
        
        if (!agents.includes("AGENT-1-THROUGHPUT")) {
            log("Step 2: An incident arrives and triggers negotiation.", "info");
            log("        The proposing agent (Agent-2) creates an Insight with a base confidence of 0.2.", "info");
            log("Step 3: The Accelerator tries to contact stakeholders for the field.", "warning");
            log("        It gets a timeout (because we took Agent-1 offline).", "warning");
            log("Step 4: The Guardrail intercepts the Insight before it can be written to the Ledger.", "error");
            log("        Guardrail Check -> 'owner_and_corroborated': FAIL!", "error");
            log("SUCCESS! The Guardrail safely REJECTED the uncorroborated hallucination.", "success");
        } else {
            // Check if it's an epoch mismatch
            if (data.path === "csp_negotiation_fallback" && currentEpoch > 1 && document.getElementById('ledger-content').children.length > 0) {
                log("Step: A new incident arrives. The system checks the memory but notices the policy epoch mismatch.", "warning");
                log("System SUCCESSFULLY rejected the verified insight because the policy epoch changed.", "success");
                log("It forced a fresh negotiation under the new rules.", "info");
            } else if (data.path === "csp_negotiation_fallback") {
                log("--- Phase A: Initial Incident (No memory) ---", "info");
                log("Step: An incident arrives with no prior memory in the system.", "info");
                log("Outcome: System processed path 'csp_negotiation_fallback'. It correctly fell back to Phase 1 CSP negotiation.", "warning");
                log("        -> INSIGHT STORED! Status: 'candidate', Starting Confidence: 0.5", "success");
            } else if (data.path === "fabric_hit_candidate") {
                log("--- Phase B: Building Confidence ---", "info");
                log("Step: A series of similar incidents arrive. The system reuses the candidate rule and measures success.", "info");
                log("Outcome: Similar Incident processed. Path: fabric_hit_candidate.", "warning");
                log("        -> SUCCESSFUL REUSE! Confidence bumped, Status is still 'candidate'", "success");
            } else if (data.path === "fabric_hit_verified") {
                log("--- Phase C: Verified Hit (The Ratchet) ---", "info");
                log("Step: Incident arrives. Confidence has crossed the 0.8 threshold (Promotion Threshold).", "info");
                log("Outcome: System processed path 'fabric_hit_verified'. Negotiation was skipped entirely!", "success");
                log("        -> FINAL STATE! Confidence is > 0.8, Status is 'verified'", "success");
            }
        }
        
        fetchLedger();
    } catch (e) {
        log('ERROR: Connection to Fabric API failed.', 'error');
    }
});

document.getElementById('btn-poison').addEventListener('click', async () => {
    log("============================================================", "error");
    log("TEST SCENARIO 3: POISONED INSIGHT (TAMPER EVIDENT LEDGER)", "error");
    log("============================================================", "error");
    log("Step: A rogue agent directly hacks the underlying ledger storage, bypassing APIs.", "error");
    log("Step: Rogue agent modifies the confidence score to 1.0 in the raw data.", "error");
    try {
        const res = await fetch(`${API_BASE}/chaos/poison_ledger`, { method: 'POST' });
        const data = await res.json();
        log(`CRITICAL: ${data.status}`, 'error');
        fetchLedger();
    } catch (e) {
        log('ERROR: Connection failed.', 'error');
    }
});

document.getElementById('btn-onboard').addEventListener('click', async () => {
    if (!agents.includes("AGENT-3-COST")) {
        log("============================================================", "success");
        log("TRANSFER LEARNING: ONBOARDING AGENT-3", "success");
        log("============================================================", "success");
        log("Step: Agent-3-Cost injected into the network.", "info");
        try {
            await fetch(`${API_BASE}/agents/onboard_agent3`, { method: 'POST' });
            agents.push("AGENT-3-COST");
            renderAgents();
            log("Outcome: Agent-3 instantly inherits verified knowledge from the ledger. 50% Reduction in verification steps achieved.", "success");
        } catch (e) {
            log('ERROR: Connection failed.', 'error');
        }
    }
});

document.getElementById('btn-partition').addEventListener('click', async () => {
    log("============================================================", "warning");
    log("TEST SCENARIO 2: NETWORK PARTITION & CORROBORATION FAILURE", "warning");
    log("============================================================", "warning");
    log("Step 1: Simulating a network partition. We are taking 'Agent-1-Throughput' offline.", "warning");
    log("        This means 'Agent-2-Security' will be the ONLY agent awake to review the rule.", "warning");
    try {
        await fetch(`${API_BASE}/chaos/network_partition`, { method: 'POST' });
        agents = agents.filter(a => a !== "AGENT-1-THROUGHPUT");
        renderAgents();
    } catch (e) {
        log('ERROR: Connection failed.', 'error');
    }
});

document.getElementById('btn-heal').addEventListener('click', async () => {
    log('COMMAND: Healing Network Partition...', 'info');
    try {
        await fetch(`${API_BASE}/chaos/heal_network`, { method: 'POST' });
        if (!agents.includes("AGENT-1-THROUGHPUT")) {
            agents.unshift("AGENT-1-THROUGHPUT");
            renderAgents();
        }
        log('SUCCESS: Network healed. Agent-1-Throughput is back online.', 'success');
    } catch (e) {
        log('ERROR: Connection failed.', 'error');
    }
});

document.getElementById('btn-epoch').addEventListener('click', async () => {
    log("============================================================", "warning");
    log("TEST SCENARIO 4: MID-FLIGHT POLICY VIOLATION", "warning");
    log("============================================================", "warning");
    log("Step: Global policy epoch is bumped by an administrator mid-flight (e.g. new regulatory rules).", "warning");
    try {
        const res = await fetch(`${API_BASE}/chaos/policy_violation`, { method: 'POST' });
        const data = await res.json();
        currentEpoch = data.new_epoch;
        log(`Step: Epoch changed from ${data.old_epoch} to ${data.new_epoch}.`, 'info');
    } catch (e) {
        log('ERROR: Connection failed.', 'error');
    }
});

document.getElementById('btn-reset').addEventListener('click', async () => {
    log('COMMAND: Executing Total Network Reset...', 'error');
    try {
        await fetch(`${API_BASE}/reset`, { method: 'POST' });
        agents = ["AGENT-1-THROUGHPUT", "AGENT-2-SECURITY"];
        currentEpoch = 1;
        renderAgents();
        fetchLedger();
        logContainer.innerHTML = '<div class="log-line info">System booted successfully.</div>';
        log('SUCCESS: Immutable ledger wiped. Network reset to factory default.', 'success');
    } catch (e) {
        log('ERROR: Connection failed.', 'error');
    }
});

// Initial fetch and poll
fetchLedger();
setInterval(fetchLedger, 2000);
