import re
from typing import Any, Dict, List, Tuple


PURPOSE_QUESTION = (
    "What is the purpose of buying this laptop? "
)


GAMING_KEYWORDS = {
    "gaming",
    "gamer",
    "game",
    "esports",
    "streaming",
    "fortnite",
    "valorant",
    "pubg",
    "battlefield",
    "cod",
    "minecraft",
    "cyberpunk",
    "witcher",
    "assassin",
}

NORMAL_USE_KEYWORDS = {
    "office",
    "personal",
    "simple",
    "everyday",
    "normal",
    "study",
    "school",
    "college",
    "business",
    "work",
    "browse",
    "browsing",
    "homework",
    "assignments",
    "note",
    "notes",
    "document",
    "documents",
    "email",
    "presentation",
    "presentations",
}

PROFESSIONAL_KEYWORDS = {
    "professional",
    "profession",
    "coding",
    "developer",
    "programming",
    "editing",
    "creator",
    "design",
    "photo editing",
    "video editing",
    "video editor",
    "photo editor",
    "developer",
    "software",
    "engineering",
    "engineer",
    "data science",
    "datascience",
    "machine learning",
    "ai",
    "ml",
}

HEAVY_GPU_KEYWORDS = ("rtx", "gtx", "rx ", "rx-", "mx ")
LIGHT_GPU_KEYWORDS = ("integrated", "intel iris", "intel uhd", "adreno", "mali", "apple gpu")


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _to_int(value: Any) -> int:
    digits = re.findall(r"\d+", str(value or ""))
    return int(digits[0]) if digits else 0


def _extract_storage_gb(value: Any) -> int:
    text = str(value or "").upper().replace(" ", "")
    amount = _to_int(text)
    if amount == 0:
        return 0
    if "TB" in text:
        return amount * 1024
    return amount


def _cpu_tier(value: Any) -> int:
    text = _normalize_text(value)

    intel_match = re.search(r"\bi\s*(3|5|7|9)\b", text)
    if intel_match:
        return int(intel_match.group(1))

    ryzen_match = re.search(r"\bryzen\s*(3|5|7|9)\b", text)
    if ryzen_match:
        return int(ryzen_match.group(1))

    if "apple" in text or "m1" in text or "m2" in text or "m3" in text:
        return 7

    return 0


def _gpu_tier(value: Any) -> int:
    text = _normalize_text(value)

    if any(keyword in text for keyword in LIGHT_GPU_KEYWORDS):
        return 0

    mx_match = re.search(r"\bmx\s*(\d{3})\b", text)
    if mx_match:
        return 1

    if re.search(r"\bgtx\s*\d{4}\b", text):
        return 2

    if re.search(r"\brtx\s*\d{4}\b", text):
        return 3

    if re.search(r"\brx\s*\d{4}\b", text):
        return 3

    if any(keyword in text for keyword in ("dedicated", "discrete")):
        return 2

    if any(keyword in text for keyword in HEAVY_GPU_KEYWORDS):
        return 2

    if text:
        return 1

    return 0


def _detect_purpose(user_input: str) -> str:
    text = _normalize_text(user_input)

    if not text:
        return "unknown"

    if any(keyword in text for keyword in GAMING_KEYWORDS):
        return "gaming"

    if any(keyword in text for keyword in PROFESSIONAL_KEYWORDS):
        return "professional"

    if any(keyword in text for keyword in NORMAL_USE_KEYWORDS):
        return "normal"

    t = text.lower()
    
    # Smart interpretation for any user input
    if any(w in t for w in ["game", "gaming", "gamer", "pubg", "valorant", "fortnite", "minecraft", "rtx", "gtx", "stream", "streaming"]):
        return "gaming"
    
    if any(w in t for w in ["work", "office", "business", "professional", "coding", "programming", "developer", "design", "editing", "photo", "video", "ml", "ai", "data", "software"]):
        return "professional"

    return "normal"


def _purpose_message(purpose: str) -> str:
    if purpose == "gaming":
        return "Gaming laptops selected: higher GPU, stronger CPU, and 16GB+ RAM are preferred."
    if purpose == "professional":
        return "Professional-use laptops selected: stronger CPU and balanced RAM with no unnecessary heavy GPU bias."
    if purpose == "normal":
        return "Normal-use laptops selected: lighter machines with integrated or low-power graphics are preferred."
    return PURPOSE_QUESTION


def _clarification_questions() -> List[Dict[str, Any]]:
    return [
        {
            "question": PURPOSE_QUESTION,
            "options": [],
        }
    ]


def _profile_filters(purpose: str) -> List[str]:
    base = ["category", "rating"]
    if purpose == "gaming":
        return base + ["GPU", "RAM", "CPU", "Storage"]
    if purpose == "professional":
        return base + ["CPU", "RAM", "Storage", "GPU"]
    if purpose == "normal":
        return base + ["GPU", "RAM", "Storage Type", "CPU"]
    return base


def _is_heavy_gpu(value: Any) -> bool:
    return _gpu_tier(value) >= 2


def _is_light_gpu(value: Any) -> bool:
    return _gpu_tier(value) <= 0


def _score_candidate(candidate: Dict[str, Any], purpose: str, budget: int) -> float:
    rating = float(candidate.get("rating", 0) or 0)
    price = int(candidate.get("price", 0) or 0)
    ram = _to_int(candidate.get("RAM", ""))
    storage_gb = _extract_storage_gb(candidate.get("Storage", ""))
    cpu = _cpu_tier(candidate.get("CPU", ""))
    gpu = _gpu_tier(candidate.get("GPU", ""))
    storage_type = _normalize_text(candidate.get("Storage Type", ""))

    score = rating * 20
    score += max(0, 20 - min(price / 25000, 20))

    if budget > 0 and price <= budget:
        score += 15
    elif budget > 0 and price > budget:
        score -= min((price - budget) / 25000, 15)

    if purpose == "gaming":
        score += gpu * 14
        score += min(ram, 32) / 2
        score += cpu * 2
        if storage_gb >= 512:
            score += 6
    elif purpose == "professional":
        score += cpu * 5
        score += min(ram, 32) * 1.2
        if storage_gb >= 512:
            score += 6
        if "ssd" in storage_type or "nvme" in storage_type:
            score += 6
        score -= gpu * 2
    elif purpose == "normal":
        score += max(0, 18 - gpu * 8)
        score += min(ram, 16) * 1.3
        if "ssd" in storage_type or "nvme" in storage_type:
            score += 8
        if storage_gb >= 256:
            score += 4
    else:
        score += cpu * 2 + gpu * 4 + min(ram, 16)
        if "ssd" in storage_type or "nvme" in storage_type:
            score += 4

    return round(score, 2)


def _passes_purpose(candidate: Dict[str, Any], purpose: str, budget: int) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    category = _normalize_text(candidate.get("category", ""))
    rating = float(candidate.get("rating", 0) or 0)
    price = int(candidate.get("price", 0) or 0)
    ram = _to_int(candidate.get("RAM", ""))
    cpu = _cpu_tier(candidate.get("CPU", ""))
    gpu = _gpu_tier(candidate.get("GPU", ""))
    storage_gb = _extract_storage_gb(candidate.get("Storage", ""))
    storage_type = _normalize_text(candidate.get("Storage Type", ""))

    if category and category != "laptop":
        reasons.append("Only laptop candidates are included for this purpose flow.")

    if rating and rating < 3.5:
        reasons.append("Rating is below the minimum 3.5-star threshold.")

    if budget > 0 and price > budget:
        reasons.append("Price exceeds the provided budget.")

    if purpose == "gaming":
        if ram and ram < 16:
            reasons.append("RAM is below the 16GB gaming baseline.")
        if cpu and cpu < 5:
            reasons.append("CPU tier is below the gaming baseline.")
        if gpu < 2:
            reasons.append("GPU is too light for a gaming laptop.")
        if storage_gb and storage_gb < 512:
            reasons.append("Storage is below the preferred gaming capacity.")
    elif purpose == "professional":
        if cpu and cpu < 5:
            reasons.append("CPU is below the professional-use baseline.")
        if ram and ram < 8:
            reasons.append("RAM is below the professional-use baseline.")
        if storage_gb and storage_gb < 256:
            reasons.append("Storage is too small for professional use.")
    elif purpose == "normal":
        if ram and ram < 8:
            reasons.append("RAM is below the normal-use baseline.")
        if _is_heavy_gpu(candidate.get("GPU", "")):
            reasons.append("Heavy GPU is unnecessary for office or personal use.")
        if storage_type and storage_type not in {"ssd", "nvme ssd", "nvme"}:
            reasons.append("SSD storage is preferred for normal laptops.")
    else:
        if ram and ram < 8:
            reasons.append("RAM is below the baseline for a general laptop shortlist.")

    return len(reasons) == 0, reasons


def _dedupe_candidates(candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    seen = {}
    duplicates_removed = 0

    for item in candidates:
        key = (
            _normalize_text(item.get("name", "")),
            int(item.get("price", 0) or 0),
        )
        existing = seen.get(key)
        if existing is None or float(item.get("score", 0) or 0) > float(existing.get("score", 0) or 0):
            if existing is not None:
                duplicates_removed += 1
            seen[key] = item
        else:
            duplicates_removed += 1

    deduped = list(seen.values())
    return deduped, duplicates_removed


def filter_agent(search_result: Dict[str, Any], input_result: Dict[str, Any], user_input: str = "") -> Dict[str, Any]:
    candidates = list(search_result.get("candidates", []) or [])
    purpose = _detect_purpose(user_input)
    budget = int(input_result.get("price", 0) or 0)

    if not candidates:
        return {
            "totalFiltered": 0,
            "filterMode": "no_match",
            "message": "No search candidates were available to filter.",
            "filteredResults": None,
            "filteredCandidates": [],
            "filtersApplied": _profile_filters(purpose),
            "filtersSkipped": [],
            "rejectedCount": 0,
            "rejectionLog": [],
            "duplicatesRemoved": 0,
            "purposeApplied": purpose,
            "needsClarification": purpose == "unknown",
            "clarificationQuestions": _clarification_questions() if purpose == "unknown" else [],
            "filter_debug_snapshot": {
                "input_fields": {
                    "category": input_result.get("category", ""),
                    "price": budget,
                    "RAM": input_result.get("RAM", ""),
                    "CPU": input_result.get("CPU", ""),
                    "GPU": input_result.get("GPU", ""),
                },
                "active_filters_count": 0,
                "candidates_received": 0,
                "rejection_reasons_total": 0,
                "final_mode": "no_match",
                "purpose": purpose,
            },
        }

    scored_candidates: List[Dict[str, Any]] = []
    rejection_log: List[Dict[str, Any]] = []
    rejected_count = 0

    for candidate in candidates:
        passes, reasons = _passes_purpose(candidate, purpose, budget)
        if not passes:
            rejected_count += 1
            rejection_log.append(
                {
                    "product": candidate.get("name", ""),
                    "reasons": reasons,
                }
            )
            continue

        scored_candidate = dict(candidate)
        scored_candidate["score"] = _score_candidate(candidate, purpose, budget)
        scored_candidate["purposeMatch"] = purpose if purpose != "unknown" else "general"
        scored_candidates.append(scored_candidate)

    if not scored_candidates:
        # Keep a soft fallback when purpose cannot be determined.
        fallback_candidates = []
        if purpose == "unknown":
            for candidate in candidates:
                fallback = dict(candidate)
                fallback["score"] = _score_candidate(candidate, "unknown", budget)
                fallback["purposeMatch"] = "general"
                fallback_candidates.append(fallback)
            scored_candidates = fallback_candidates
        else:
            return {
                "totalFiltered": 0,
                "filterMode": "no_match",
                "message": _purpose_message(purpose),
                "filteredResults": None,
                "filteredCandidates": [],
                "filtersApplied": _profile_filters(purpose),
                "filtersSkipped": [],
                "rejectedCount": rejected_count,
                "rejectionLog": rejection_log,
                "duplicatesRemoved": 0,
                "purposeApplied": purpose,
                "needsClarification": False,
                "clarificationQuestions": [],
                "filter_debug_snapshot": {
                    "input_fields": {
                        "category": input_result.get("category", ""),
                        "price": budget,
                        "RAM": input_result.get("RAM", ""),
                        "CPU": input_result.get("CPU", ""),
                        "GPU": input_result.get("GPU", ""),
                    },
                    "active_filters_count": len(_profile_filters(purpose)),
                    "candidates_received": len(candidates),
                    "rejection_reasons_total": sum(len(item.get("reasons", [])) for item in rejection_log),
                    "final_mode": "no_match",
                    "purpose": purpose,
                },
            }

    deduped_candidates, duplicates_removed = _dedupe_candidates(scored_candidates)
    deduped_candidates.sort(key=lambda item: (float(item.get("score", 0) or 0), float(item.get("rating", 0) or 0)), reverse=True)

    filters_applied = _profile_filters(purpose)
    filters_skipped = [field for field in ["Generation", "StoreName", "Location"] if field not in filters_applied]

    clarification_needed = purpose == "unknown"
    mode = "near_match" if clarification_needed else "exact_filter"

    return {
        "totalFiltered": len(deduped_candidates),
        "filterMode": mode,
        "message": _purpose_message(purpose),
        "filteredResults": deduped_candidates[0] if deduped_candidates else None,
        "filteredCandidates": deduped_candidates,
        "filtersApplied": filters_applied,
        "filtersSkipped": filters_skipped,
        "rejectedCount": rejected_count,
        "rejectionLog": rejection_log,
        "duplicatesRemoved": duplicates_removed,
        "purposeApplied": purpose,
        "needsClarification": clarification_needed,
        "clarificationQuestions": _clarification_questions() if clarification_needed else [],
        "filter_debug_snapshot": {
            "input_fields": {
                "category": input_result.get("category", ""),
                "price": budget,
                "RAM": input_result.get("RAM", ""),
                "CPU": input_result.get("CPU", ""),
                "GPU": input_result.get("GPU", ""),
            },
            "active_filters_count": len(filters_applied),
            "candidates_received": len(candidates),
            "rejection_reasons_total": sum(len(item.get("reasons", [])) for item in rejection_log),
            "final_mode": mode,
            "purpose": purpose,
        },
    }


def filter_products_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("error"):
        return {}

    try:
        return {
            "filter_result": filter_agent(
                state.get("search_result", {}),
                state.get("input_result", {}),
                state.get("user_input", ""),
            )
        }
    except Exception as exc:
        return {
            "filter_result": {
                "totalFiltered": 0,
                "filterMode": "no_match",
                "message": f"filter_agent_failed: {exc}",
                "filteredResults": None,
                "filteredCandidates": [],
                "filtersApplied": [],
                "filtersSkipped": [],
                "rejectedCount": 0,
                "rejectionLog": [],
                "duplicatesRemoved": 0,
                "purposeApplied": "unknown",
                "needsClarification": True,
                "clarificationQuestions": _clarification_questions(),
                "filter_debug_snapshot": {
                    "input_fields": {},
                    "active_filters_count": 0,
                    "candidates_received": 0,
                    "rejection_reasons_total": 0,
                    "final_mode": "no_match",
                    "purpose": "unknown",
                },
            },
            "error": f"filter_agent_failed: {exc}",
        }
