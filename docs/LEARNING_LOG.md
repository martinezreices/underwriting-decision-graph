# Learning Log – Policy Decision Graph

## Concept: Shared State in LangGraph
What I understood:
- There is one explicit dictionary (`PolicyDecisionState`) that travels through every node.
- Every node reads from this state and writes its results back into it.
- This creates a single source of truth for the entire decision.

Why it matters for Decision Engineering:
- Makes the system auditable — you can always see exactly what information was available at each step.
- Prevents hidden coupling between functions.
- Makes it much easier to add observability (LangSmith) and evaluation later.
- Interviewers often ask how you manage state in multi-step decision systems; this is a clear, modern answer.

## Concept: Pure Node Functions
What I understood:
- Each node is a function that receives the full state and returns the updated state.
- Nodes should avoid hidden side effects (no global variables, no sneaky database calls in v1).
- This makes every step independently testable and replaceable.

Why it matters for Decision Engineering:
- You can unit-test one node without running the whole pipeline.
- You can later swap a simple rule-based node for a real model or LLM call without rewriting the graph.
- It forces clean interfaces — a hallmark of production-grade systems.

## Concept: Layered Decision Design (Rules → Models → LLM)
What I understood:
- Data Quality checks come first (Intake).
- Deterministic business rules come next (Hard Guardrails).
- Only then do we apply a model score.
- Finally we add confidence and a refined explanation.
- Human handoff can be triggered at multiple layers.

Why it matters for Decision Engineering:
- High-reliability systems do not rely only on LLMs or models.
- Clear rules handle the obvious “no” cases cheaply and explainably.
- Models and LLMs are used where they add real value.
- This layered approach is exactly what Decision Engineering / AI Systems Lead roles look for.

## Concept: Early Data Quality Checks
What I understood:
- Bad or incomplete data should be caught at the very first node.
- We record specific errors and immediately set `human_handoff = True`.
- We treat data-quality failures differently from business-rule failures.

Why it matters for Decision Engineering:
- Most decision failures in production start with bad data.
- Catching problems early reduces noise for later nodes and for human reviewers.
- It creates a cleaner audit trail and makes the system more trustworthy.

## Mistakes & Corrections
- Used wrong date format (`%y` instead of `%Y`) in Enrichment → fixed.
- Case-sensitivity bug in allowed Lines of Business (`"commercial Property"` vs `"Commercial Property"`) → fixed.
- `final_score` was not appearing in the final output because of how `structured_output` was written → fixed.
- Learned that small typos in state keys (e.g. capital letters) silently break downstream logic.
- Realized the importance of always initializing lists/dicts safely (`or []` / `or {}`) to avoid type errors.