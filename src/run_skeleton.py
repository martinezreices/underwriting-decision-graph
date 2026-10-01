from graph import graph
import json


# sample_policy = {
#     "policy_id": "POL-1001",
#     "insured_name": "Acme Manufacturing Ltd",
#     "policy_number": "PR-2026-88421",
#     "status": "Active",
#     "line_of_business": "Commercial Property",
#     "exposure_category": "Light Industrial",
#     "effective_date": "2026-01-15",
#     "expiration_date": "2027-01-14",
#     "gwp_usd": 125000.0,
#     "commission_rate": 12.5,
#     "enrichment": {},
#     "guardrail_flags": [],
#     "model_score": None,
#     "model_explanation": None,
#     "llm_refinement": None,
#     "final_score": None,
#     "confidence": None,
#     "human_handoff": False,
#     "handoff_reason": None,
#     "final_output": {},
#     "errors": [],
#     "trace_id": None,
# }

# broken_policy = {
#     "policy_id": "POL-9999",
#     "insured_name": "",                          # empty
#     "policy_number": "PR-999",
#     "status": "UnknownStatus",                   # invalid
#     "line_of_business": "Commercial Property",
#     "exposure_category": "Light Industrial",
#     "effective_date": "2027-01-15",              # after expiration
#     "expiration_date": "2026-01-14",
#     "gwp_usd": -5000,                            # negative
#     "commission_rate": 150,                      # > 100
#     "enrichment": {},
#     "guardrail_flags": [],
#     "model_score": None,
#     "model_explanation": None,
#     "llm_refinement": None,
#     "final_score": None,
#     "confidence": None,
#     "human_handoff": False,
#     "handoff_reason": None,
#     "final_output": {},
#     "errors": [],
#     "trace_id": None,
# }

failure_policy = {
    "policy_id": "POL-FAIL-001",
    "insured_name": "Risky Operations LLC",
    "policy_number": "PR-FAIL-999",
    "status": "Active",
    "line_of_business": "Cyber Liability",          # Not in allowed list
    "exposure_category": "Chemical",                # Restricted
    "effective_date": "2026-01-15",
    "expiration_date": "2026-10-01",                # Relatively soon
    "gwp_usd": 750000,                              # Above max threshold
    "commission_rate": 18.0,
    
    # Required state defaults
    "enrichment": {},
    "guardrail_flags": [],
    "model_score": None,
    "model_explanation": None,
    "llm_refinement": None,
    "final_score": None,
    "confidence": None,
    "human_handoff": False,
    "handoff_reason": None,
    "final_output": {},
    "errors": [],
    "trace_id": None,
}

print("Running Policy Decision Graph (skeleton)...")
print("-" * 60)

result = graph.invoke(failure_policy)

print("-" * 60)
print("Final Output:")
print(json.dumps(result["final_output"], indent=2))
print("\nFull final state keys:", list(result.keys()))
print("\nEnrichment data:")
print(result.get("enrichment"))
print("\nModel Score:", result.get("model_score"))
print("Model Explanation:", result.get("model_explanation"))
print("\nConfidence:", result.get("confidence"))
print("LLM Refinement:", result.get("llm_refinement"))