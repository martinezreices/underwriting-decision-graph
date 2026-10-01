# Policy Decision Graph v1 – Progress Log

## Project Goal
Build an end-to-end LangGraph underwriting decision pipeline that demonstrates:
- Explicit shared state
- Layered intelligence (rules → models → LLM)
- Data quality + business guardrails
- Human handoff
- Observability & evaluation readiness

This project simultaneously builds Decision Engineering skills and core Data Engineering skills.

---

## Phase 1 – Design & Contract
**Status:** Completed

- Defined decision contract
- Created canonical state schema (`PolicyDecisionState`)
- Created sample policies (clean + broken)

**Key Learning:**
- Explicit contracts prevent scope creep and make systems explainable.

---

## Phase 2 – Thin Graph Skeleton
**Status:** Completed

- Built LangGraph with 7 nodes
- Wired sequential edges
- Confirmed end-to-end execution with sample data

**Key Learning:**
- Starting with a runnable skeleton forces composition thinking early.
- Pure node functions + shared state make the system testable and auditable.

---

## Phase 3 – Intelligence Nodes (In Progress)

### 3.1 Intake & Normalize + Data Quality
**Status:** Completed

What was implemented:
- Required field checks
- Type and range validation (GWP, commission rate)
- Basic date validation
- Status normalization
- Errors written into state
- Automatic human handoff on data quality failure

**Key Learning:**
- Data quality should be enforced as early as possible.
- Separating “data is unusable” from “business rule violation” creates clearer systems.

**Evidence:**
- Clean policy → no flags, human_handoff = false
- Broken policy → multiple DATA_QUALITY flags + human_handoff = true

...

### 3.2 Hard Guardrails (Business Rules)
**Status:** Completed

What was implemented:
- Line of Business validation (allowed list)
- GWP minimum and maximum thresholds
- Near-expiration flag (< 30 days)
- Restricted exposure categories (Heavy Industrial, Chemical, High Hazard)
- Clear BUSINESS_RULE flags + forced human handoff  - Humman in the Middle Review

**Key Learning:**
- Deterministic business rules should sit in front of models.
- Separating data-quality failures from appetite/business-rule failures makes the system easier to explain and audit.

**Evidence:**
- Clean policy → no business-rule flags
- Violation policy → multiple BUSINESS_RULE flags + human_handoff = true

...

### 3.3 Final Aggregation
**Status:** Completed

What was implemented:
- Sets final_score from the model score
- Applies final human-handoff rules (low confidence or any remaining flags)
- Writes the definitive human_handoff and handoff_reason

**Key Learning:**
- There should be one clear place where the system makes the final decision about automatic vs human review.

...
### 3.4 Model Evaluation
**Status:** Completed

What was implemented:
- Transparent rule-based scoring (0–100)
- Uses both raw fields and enriched features
- Produces model_score and model_explanation

**Key Learning:**
- Even a simple, transparent model is valuable when the surrounding pipeline is solid.
- The node pattern (read state → write score + explanation) is ready to be replaced later with a real model factory call.

...
### 3.5 LLM Explanation & Confidence
**Status:** Completed

What was implemented:
- Confidence calculation based on flags and score extremity
- Rule-based refinement of the explanation (placeholder for a real LLM later)

**Key Learning:**
- Confidence should be an explicit, first-class output of the decision system.
- Keeping the refinement step separate makes it easy to swap in a real LLM later without touching the rest of the pipeline.

---

## Decisions Log

| Date | Decision | Why |
|------|----------|-----|
| 2026-08-25 | Use sequential edges for v1 | Simplicity and predictability while learning |
| 2026-08-26 | Separate Data Quality from Business Rules | Different concerns, easier to test and explain |
| 2026-09-23 | Full v1 pipeline working end-to-end | All seven nodes now produce a coherent decision
| | | |

---

## Open Questions / Next Focus
- Review and add print statements in milestone areas