import json
from typing import Any, Dict, List

from langchain_ollama import OllamaLLM

from advisor_tools import generate_usage_tips_tool, validate_recommendation_fit_tool


llm = OllamaLLM(model="llama3")


def _safe_alternatives(
    filter_result: Dict[str, Any],
    selected_name: str,
    limit: int = 2,
) -> List[Dict[str, Any]]:
    """
    Pick up to `limit` alternatives from filtered candidates excluding selected.
    """

    alternatives: List[Dict[str, Any]] = []
    for item in list(filter_result.get("filteredCandidates", []) or []):
        if str(item.get("name", "")) == selected_name:
            continue
        alternatives.append(
            {
                "name": item.get("name", ""),
                "price": item.get("price", 0),
                "rating": item.get("rating", 0),
                "reason": "Alternative from filtered shortlist with strong overall match.",
            }
        )
        if len(alternatives) >= limit:
            break
    return alternatives


def _improvement_suggestions(validation: Dict[str, Any], constraints: Dict[str, Any]) -> List[str]:
    """
    Build practical improvement suggestions from mismatch fields.
    """

    suggestions: List[str] = []
    for mismatch in validation.get("mismatches", []):
        field = str(mismatch.get("field", ""))
        if field == "price":
            suggestions.append("Increase budget slightly or relax one high-cost hardware constraint.")
        elif field == "GPU":
            suggestions.append("Relax GPU tier if you want more affordable options.")
        elif field == "CPU":
            suggestions.append("Consider a broader CPU range (e.g., i5/Ryzen 5 and above).")
        elif field in {"RAM", "Storage"}:
            suggestions.append("Lower minimum RAM/storage requirement if more options are needed.")
        elif field == "brand":
            suggestions.append("Allow additional brands to improve candidate diversity.")

    if not suggestions and int(constraints.get("price", 0) or 0) > 0:
        suggestions.append("If available, increase budget by 5-10% for newer generation options.")
    if not suggestions:
        suggestions.append("Current requirements are well balanced; compare warranty and store location before buying.")

    return suggestions[:3]


def recommendation_advisor_agent(
    input_result: Dict[str, Any],
    filter_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Final recommendation advisor after deterministic filter stage.

    Uses:
    - Custom tool: validate_recommendation_fit_tool
    - Custom tool: generate_usage_tips_tool
    - LLM (guardrailed) for concise rationale generation
    """

    filtered_candidates = list(filter_result.get("filteredCandidates", []) or [])
    if not filtered_candidates:
        return {
            "fit_status": "no_fit",
            "fit_score": 0,
            "selected_product": None,
            "why_selected": [],
            "mismatches": [{"field": "availability", "required": "at least 1 candidate", "actual": "0 candidates"}],
            "alternatives": [],
            "improvement_suggestions": [
                "Relax one or two strict constraints (brand/GPU/budget).",
                "Increase budget range to unlock better matches.",
            ],
            "usage_tips": [],
            "confidence": "low",
        }

    selected = filtered_candidates[0]
    validation = validate_recommendation_fit_tool(input_result, selected)
    usage_tips = generate_usage_tips_tool(selected, input_result.get("category", ""))
    alternatives = _safe_alternatives(filter_result, str(selected.get("name", "")))
    suggestions = _improvement_suggestions(validation, input_result)

    prompt = f"""
You are Recommendation Advisor Agent.
You must explain product recommendation using ONLY provided facts.
Do not hallucinate. Output ONLY valid JSON.

User constraints:
{json.dumps(input_result, ensure_ascii=True)}

Selected candidate:
{json.dumps(selected, ensure_ascii=True)}

Validation details:
{json.dumps(validation, ensure_ascii=True)}

Required JSON format:
{{
  "why_selected": ["..."],
  "confidence": "low|medium|high"
}}
"""

    why_selected = list(validation.get("matched_reasons", []))
    confidence = "high" if validation.get("fit_score", 0) >= 85 else "medium"

    try:
        llm_response = llm.invoke(prompt)
        llm_json = json.loads(str(llm_response).strip())
        if isinstance(llm_json.get("why_selected"), list) and llm_json["why_selected"]:
            why_selected = [str(item) for item in llm_json["why_selected"]][:5]
        if str(llm_json.get("confidence", "")).lower() in {"low", "medium", "high"}:
            confidence = str(llm_json["confidence"]).lower()
    except Exception:
        # Fallback keeps output stable when local model is unavailable.
        pass

    return {
        "fit_status": validation.get("fit_status", "partial_fit"),
        "fit_score": int(validation.get("fit_score", 0) or 0),
        "selected_product": {
            "name": selected.get("name", ""),
            "price": selected.get("price", 0),
            "rating": selected.get("rating", 0),
            "category": selected.get("category", ""),
        },
        "why_selected": why_selected,
        "mismatches": validation.get("mismatches", []),
        "alternatives": alternatives,
        "improvement_suggestions": suggestions,
        "usage_tips": usage_tips,
        "confidence": confidence,
    }
