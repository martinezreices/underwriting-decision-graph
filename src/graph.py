from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END

# -------------------------------------------------
# Shared State Schema
# -------------------------------------------------
class PolicyDecisionState(TypedDict): # AgentState
    # Raw / normalized policy fields
    policy_id: str
    insured_name: str
    policy_number: str
    status: str
    line_of_business: str
    exposure_category: str
    effective_date: str
    expiration_date: str
    gwp_usd: float
    commission_rate: float

    # Enrichment & intermediate results
    enrichment: Dict[str, Any]
    guardrail_flags: List[str]
    model_score: Optional[float]
    model_explanation: Optional[str]
    llm_refinement: Optional[str]

    # Final decision fields
    final_score: Optional[float]
    confidence: Optional[float]
    human_handoff: bool
    handoff_reason: Optional[str]
    final_output: Dict[str, Any]

    # Optional metadata
    errors: List[str]
    trace_id: Optional[str]


# -------------------------------------------------
# Node stub functions (pure)
# -------------------------------------------------
def intake_normalize(state: PolicyDecisionState) -> PolicyDecisionState:
    print("→ Node: Intake & Normalize")
    

    # 1. Problem Collection
    # -------------------------------------------------------------------   
    errors = list(state.get("errors") or [])
    flags = list(state.get("guardrail_flags") or [])

    # 2. Required Fields
    # -------------------------------------------------------------------   
    required_fields = [
        "policy_id",
        "insured_name",
        "policy_number",
        "status",
        "line_of_business",
        "exposure_category",
        "effective_date",
        "expiration_date",
        "gwp_usd",
        "commission_rate"
    ]

    for field in required_fields:
        value = state.get(field)
        if value is None or (isinstance(value, str) and value.strip() ==""):
            errors.append(f"Missing or empty required field: {field}")


    # 3. Type and Value Checks
    # -------------------------------------------------------------------   

    # gwp_usd must be a positive number
    gwp = state.get("gwp_usd")
    try:
        gwp = float(gwp)
        if gwp <= 0:
            errors.append("gwp_usd must be greater than 0")
        state["gwp_usd"] = gwp                                  # adding clean value to state

    except (TypeError, ValueError):
        errors.append("gwp_usd must be a valid number")


    # commission_rate must be between 0 and 100
    rate = state.get("commission_rate")
    try:
        rate = float(rate)
        if rate < 0 or rate > 100:
            errors.append("commission rate must be between 0 and 100")
        state["commission_rate"] = rate                           # adding clean value to state
    except(TypeError, ValueError):
        errors.append("commission_rate must be a valid number")



    # 4. date validation 
    # -------------------------------------------------------------------   
    from datetime import datetime

    def parse_date(date_str: str, field_name: str):
        try:
            return datetime.strptime(date_str,"%Y-%m-%d")
        except(TypeError, ValueError):
            errors.append("f{field_name} is not a valid date (expected YYYY-MM-DD)")
            return None

    effective = parse_date(state.get("effective_date"), "effective_date")
    expiration = parse_date(state.get("expiration_date"), "expiration_date")

    if effective and expiration and effective >= expiration:
        errors.append("effective_date must be before expiration_date")


    # 5. status normalization
    # -------------------------------------------------------------------   

    status = str(state.get("status") or "").strip().title()
    allowed_statuses = {"Active", "Pending", "Cancelled", "Expired"}

    if status not in allowed_statuses:
        errors.append(f"{status } is not an allowed value: {allowed_statuses}")
    state["status"] = status

    

    # write results back into state
    # ------------------------------------------------------------------- 

    state["errors"] = errors

    if errors:
        # We treat data-quality failures as guardrail flags so later nodes can see them
        flags.extend([f"Data_Quality: {e}" for e in errors])
        state["guardrail_flags"] = flags
        state["human_handoff"] = True
        state["handoff_reason"] = "Data quality issues found during intake"


    return state

    print("status guardian completed review ...")


def enrichment(state: PolicyDecisionState) -> PolicyDecisionState:
    print("→ Node: Enrichment")

    enrichment_data = dict(state.get("enrichment") or {})

    from datetime import datetime

    # 1. Calculate policy duration in days
    # -------------------------------------------------------

    try:
        effective = datetime.strptime(state.get("effective_date"), "%Y-%m-%d")
        expiration = datetime.strptime(state.get("expiration_date"), "%Y-%m-%d")
        duration_days = (expiration - effective).days
        enrichment_data["policy_duration_days"] = duration_days

    except Exception:
        enrichment_data["policy_duration_days"] = None

    # 2. days until expiration 
    # ------------------------------------------------------------

    try:
        expiration = datetime.strptime(state.get("expiration_date"), "%Y-%m-%d")
        days_to_expiry = (expiration - datetime.now()).days
        enrichment_data["days_to_expiration"] = days_to_expiry

    except Exception:
        enrichment_data["days_to_expiration"] = None 


    # 3. Simple Premium Band Size
    # ---------------------------------------------------------------------

    gwp = state.get("gwp_usd") or 0

    if gwp < 25000: 
        band = "Small"
    elif gwp < 100000:
        band = "Medium"
    else:
        band = "Large"

    enrichment_data["premium_band"] = band


    # 4. Renewal candidate Flag 
    # ---------------------------------------------------------------------------

    days_to_expiry = enrichment_data.get("days_to_expiration")
    enrichment_data["is_renewal_candidate"] = (
        days_to_expiry is not None and 0 < days_to_expiry <=90
    )


    # 5. write back into state
    # -----------------------------------------------------------------------------
    state["enrichment"] = enrichment_data
    return state

def hard_guardrails(state: PolicyDecisionState) -> PolicyDecisionState:
    print("→ Node: Hard Guardrails")

    flags = list(state.get("guardrail_flags") or [])

    # 1. Allowed Lines of Business
    #-------------------------------------------------------------------------------

    allowed_lobs = {
        "Commercial Property", 
        "General Liability",
        "Commercial Auto",
        "Workers Compensation"
    }

    lob = state.get("line_of_business")
    if lob not in allowed_lobs:
        flags.append(f"BUSINESS_RULE: Line of Business {lob} not covered")

    # 2. GWP range checks
    # -------------------------------------------------------------------------------

    gwp = state.get("gwp_usd") or 0

    if gwp < 5000:
        flags.append("BUSINESS_RULE: GWP is below min threshold ($5,000)")
    elif gwp > 500000:
        flags.append("BUSINESS_RULE: GWP exceeds max threshold ($500,000)")

    # 3. Policy too close to expiration

    days_to_expiry = state.get("enrichment", {}).get("days_to_expiration")

    if days_to_expiry is not None and days_to_expiry < 30:
        flags.append(f"BUSINESS_RULE: Policy expires in {days_to_expiry} days")

    # 4. Restricted exposure Categories
    # --------------------------------------------------------------------------------

    restricted_exposures = ("Heavy Industrial", "Chemical", "High Hazard")
    exposure = state.get("exposure_category")

    if exposure in restricted_exposures:
        flags.append(f"BUSINESS_RULE: Exposure category '{exposure}' is restricted")
    

    # 5. Writing Back into state
    # -------------------------------------------------------------------------------

    state["guardrail_flags"] = flags

    # if any business-rule flag exist, force human handoff
    business_flags = [f for f in flags if f.startswith("BUSINESS_RULE:")]
    if business_flags:
        state["human_handoff"] = True
        if not state.get("handoff_reason"):
            state["handoff_reason"] = "business rule violations detected"

    return state

def model_evaluation(state: PolicyDecisionState) -> PolicyDecisionState:
    print("→ Node: Model Evaluation")

    # for this project the model evaluation will score, 
    # in production the system may skip scoring

    gwp = state.get("gwp_usd") or 0
    commission = state.get("commission_rate") or 0
    days_to_expiry = state.get("enrichment", {}).get("days_to_expiration")
    premium_band = state.get("enrichment", {}).get("premium_band")
    lob = state.get("line_of_business")

    # Simple Scoring Logic
    # --------------------------------------------------

    score = 70 # start with a neutral base score

    # adjust for premium size
    if premium_band =="Small":
        score += 10
    elif premium_band == "Large":
        score -= 5

    # Adjust for time to expiration
    if days_to_expiry is not None:
        if days_to_expiry < 60:
            score -= 10
        elif days_to_expiry >180:
            score += 5

    # adjust for line of business preference

    preferred_lobs = {"Commercial Property", "General Liability"}
    if lob in preferred_lobs:
        score += 5

    # keep score in 0-100 range
    score = max(0, min(100, score))

    # writing into state
    #---------------------------------------------------------------

    state['model_score'] = score

    state['model_explanation'] = (
        f"Base score 70, "
        f"Premium band '{premium_band}' adjustment, "
        f"commission {commission}%, "
        f"days to expiry {days_to_expiry}, "
        f"Final model score: {score}. "
    ) 

    return state

def llm_explanation_confidence(state: PolicyDecisionState) -> PolicyDecisionState:
    print("→ Node: LLM Explanation & Confidence Refinement")

    model_score = state.get("model_score")
    model_explanation = state.get("model_explanation") or ""
    flags = state.get("guardrail_flags") or []

    # 1. calculate the confidence 
    # ---------------------------------------------------------------
    confidence = 0.75  # starting confidence

    # Any guardrail flags reduce confidence
    if flags:
        confidence -= 0.15 * min(len(flags), 3)

    # Extrreme model scores are treated less reliable (over-optimistic)
    if model_score is not None: 
        if model_score < 40 or model_score > 90:
            confidence -= 0.10

    # maintaining a sensible range of confidence between .10 and .95
    confidence = max(0.10, min(0.95, confidence))
    state["confidence"] = round(confidence, 2)


    # 2. create a clearer explanation 
    # -----------------------------------------------------------------

    if model_score is None:
        refined = "No model score was produced"

    else: 
        if model_score >= 75:
            quality = "strong"
        elif model_score >= 55:
            quality = "acceptable"
        else:
            quality = "weak"

        refined = (
            f"The model produced a score of : {model_score}, which is interpreted as {quality}. "
            f"{model_explanation}"
        )

        if flags: 
            refined += f"However, {len(flags)} guardrail flag(s) were raised, which reduces overall confidence"

    state["llm_refinement"] = refined.strip()

    return state

def final_aggregation(state: PolicyDecisionState) -> PolicyDecisionState:
    print("→ Node: Final Aggregation")

    model_score = state.get("model_score")
    confidence = state.get("confidence")
    flags = state.get("guardrail_flags") or []
    human_handoff = state.get("human_handoff", False)
    handoff_reason = state.get("handoff_reason")

    # 1. Decide final score
    #------------------------------------------------------------------------
    if model_score is None:
        final_score = None
    else:
        final_score = model_score

    state["final_score"] = final_score

    # 2. Final human-handoff logic
    #------------------------------------------------------------------------
    if confidence is not None and confidence < 0.55:
        human_handoff = True
        if not handoff_reason:
            handoff_reason = "Confidence below acceptable threshold"

    if flags and not human_handoff:
        human_handoff = True
        handoff_reason = "Guardrail flags present"

    state["human_handoff"] = human_handoff
    state["handoff_reason"] = handoff_reason

    return state

def structured_output(state: PolicyDecisionState) -> PolicyDecisionState:
    print("→ Node: Structured Output")
    state["final_output"] = {
        "policy_id": state.get("policy_id"),
        "final_score": state.get("final_score"),
        "confidence": state.get("confidence"),
        "human_handoff": state.get("human_handoff", False),
        "handoff_reason": state.get("handoff_reason"),
        "guardrail_flags": state.get("guardrail_flags", []),
        "explanation": state.get("llm_refinement") or state.get("model_explanation"),
    }
    return state


# -------------------------------------------------
# Build the graph
# -------------------------------------------------
def build_graph():
    workflow = StateGraph(PolicyDecisionState)

    workflow.add_node("intake_normalize", intake_normalize)
    workflow.add_node("enrichment", enrichment)
    workflow.add_node("hard_guardrails", hard_guardrails)
    workflow.add_node("model_evaluation", model_evaluation)
    workflow.add_node("llm_explanation_confidence", llm_explanation_confidence)
    workflow.add_node("final_aggregation", final_aggregation)
    workflow.add_node("structured_output", structured_output)

    workflow.set_entry_point("intake_normalize")
    workflow.add_edge("intake_normalize", "enrichment")
    workflow.add_edge("enrichment", "hard_guardrails")
    workflow.add_edge("hard_guardrails", "model_evaluation")
    workflow.add_edge("model_evaluation", "llm_explanation_confidence")
    workflow.add_edge("llm_explanation_confidence", "final_aggregation")
    workflow.add_edge("final_aggregation", "structured_output")
    workflow.add_edge("structured_output", END)

    return workflow.compile()


graph = build_graph()