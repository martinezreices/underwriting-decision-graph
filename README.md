# Policy Decision Graph v1

This is an end-to-end decision pipeline for underwriting-style decisions, built with LangGraph.

I built it to practice the kind of systems work that actually matters in Decision Engineering / AI Systems Lead roles — not just calling an LLM, but designing a reliable flow that can handle real constraints.

The pipeline takes a policy record, cleans and validates it, applies business rules, scores it, estimates confidence, and decides whether a human needs to look at it.

---

# Why this exists

It’s easy to build something that just sends data to a model or an LLM and returns an answer. That’s usually the fastest way to get a demo working.

But in domains where decisions have real consequences (underwriting, credit, claims, etc.), that approach tends to create problems:

- Bad or incomplete data still gets scored
- There’s no clear place for hard business rules
- It’s hard to explain why a decision was made
- There’s often no explicit signal for when a human should review the case
- The whole flow becomes difficult to audit

I wanted to practice designing the system the other way around: validate first, apply clear rules, then score, then estimate confidence, and only then decide whether the case can pass through or needs a human. The goal is to keep the reasoning visible so the final decision is easier to understand and audit.

---

# How the pipeline works

```text
Policy comes in
    ↓
Intake & Normalize      → clean the data, catch obvious problems
    ↓
Enrichment              → add useful derived fields
    ↓
Hard Guardrails         → deterministic business rules / appetite checks
    ↓
Model Evaluation        → produce a score
    ↓
Confidence + Explanation
    ↓
Final Aggregation       → final score + human handoff decision
    ↓
Structured Output
```

Everything shares one explicit state object that moves through the nodes. Each node is just a function that reads the state and writes back to it.

# Design choices I care about

I kept a single shared state object that moves through every step. It makes the flow easier to follow and will make it much simpler to add proper tracing later.

Each node is just a function that takes the state and returns the updated state. These small, self-contained pieces make it easier to test and swap out later if I want to replace the simple scoring logic with something better.

I treated data quality problems and business rule violations as two different things. One means the data itself is unusable. The other means the data is fine but the risk sits outside appetite. Mixing them together usually makes the system harder to reason about.

Hard rules run before any scoring. If something is clearly outside what the business wants, there’s no need to run a model.

Human handoff is built in from the start so the system can escalate cases that need review instead of forcing everything through automatically. Same with confidence — the system has to produce a confidence value, not just a score.


# Example results

**Clean policy**
- Score: 70
- Confidence: 0.75
- Human handoff: false



**Problem policy**(wrong LOB, high premium, restricted exposure, near expiry)

- Score: 55
- Confidence: 0.30
- Human handoff: true
- Multiple clear business rule flags

Even when the case is bad, the system still returns a full result instead of just failing.

---

# Running it
```bash
python -m venv env
source env/bin/activate          # Windows: env\Scripts\activate
pip install langgraph langchain-core pydantic

cd src
python run_skeleton.py
```
---
# Current Status

Working end-to-end on both clean and failure cases.
Still missing:

- Proper observability (LangSmith)
- Real evaluation set
- Better scoring model
- Tests
- Conditional routing when hard guardrails fail early

---
# What I’m trying to demonstrate with this 

That I can design a decision system that is more than a prompt chain — one that has clear layers, handles bad data, knows when to stop and ask for a human, and stays understandable.

This is the foundation I’ll keep extending.


