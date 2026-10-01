# Architecture Decision Record – Policy Decision Graph v1

## Context

I wanted to build a decision pipeline that does more than send data to a model and return a score. The goal was to design a system that can handle messy inputs, apply clear business constraints, produce a transparent score, estimate confidence, and know when to involve a human.

This is a v1. The scope is intentionally limited so I could focus on structure and judgment rather than feature volume.

## Decision

I built the system as a sequential graph of pure nodes that share one explicit state object.

The main flow is:

1. Intake & Normalize  
2. Enrichment  
3. Hard Guardrails  
4. Model Evaluation  
5. Confidence & Explanation  
6. Final Aggregation  
7. Structured Output  

### Why a graph with shared state?

I wanted every step to be visible. Passing one shared state object through each node makes it easier to see what information was available at each point, and it sets the system up for proper tracing later. Keeping nodes as simple functions that only read and write state also makes them easier to test and replace.

### Why separate Data Quality from Business Rules?

These are different problems.

- Data quality issues mean the input itself is incomplete or invalid.  
- Business rule violations mean the data is fine, but the case sits outside appetite.  

Keeping them separate makes the system easier to reason about and explain.

### Why run hard rules before the model?

If a policy is clearly outside what the business is willing to write, there is no need to score it first. Deterministic rules are cheap, transparent, and easy to audit. The model should only run on cases that pass the basic checks.

### Why make confidence and human handoff first-class outputs?

A score alone is not enough. The system should also say how reliable that score is, and it should have a clear way to escalate cases that need review instead of forcing everything through automatically.

## Trade-offs accepted in v1

- The scoring model is still simple and rule-based. This was intentional so I could focus on pipeline structure first.  
- The flow is fully sequential — there is no early exit yet when hard guardrails fail.  
- Explanation refinement is still deterministic rather than using a real LLM.  
- There is no persistent storage or batch processing yet.  

These are deliberate constraints for v1.

## What this architecture is optimized for

- Clarity of flow  
- Auditability  
- Ability to add observability later  
- Ability to swap individual pieces (especially the scoring step)  
- Making human review a normal part of the design  

## What I would change next

- Add conditional edges so clearly invalid cases can skip scoring  
- Introduce proper tracing  
- Build a small evaluation set  
- Replace the simple scorer with a more realistic model  
- Add basic tests around the main nodes  

## Summary

Validate first, apply clear rules, then score, then estimate confidence, and only then decide whether the case can proceed or needs a human. The architecture is built to make that sequence visible and maintainable.