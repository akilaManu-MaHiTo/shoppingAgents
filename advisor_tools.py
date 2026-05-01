import re
from typing import Any, Dict, List


def _to_int(value: Any) -> int:
    """
    Convert mixed numeric text to int (e.g., "16GB" -> 16).
    Returns 0 when conversion fails.
    """

    if value is None:
        return 0
    digits = re.findall(r"\d+", str(value))
    if not digits:
        return 0
    try:
        return int(digits[0])
    except (TypeError, ValueError):
        return 0


def validate_recommendation_fit_tool(
    user_constraints: Dict[str, Any],
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate whether a candidate product fits explicit user constraints.

    Args:
        user_constraints: Parsed user requirements from input agent.
        candidate: Single candidate product from filter/search stage.

    Returns:
        Structured validation result with score and mismatch details:
        {
            "fit_score": int,
            "fit_status": str,
            "matched_reasons": List[str],
            "mismatches": List[Dict[str, Any]],
            "checks": Dict[str, bool]
        }
    """

    checks: Dict[str, bool] = {}
    matched_reasons: List[str] = []
    mismatches: List[Dict[str, Any]] = []

    req_brand = str(user_constraints.get("product", "")).strip().lower()
    req_category = str(user_constraints.get("category", "")).strip().lower()
    req_budget = int(user_constraints.get("price", 0) or 0)
    req_ram = _to_int(user_constraints.get("RAM", ""))
    req_storage = _to_int(user_constraints.get("Storage", ""))
    req_storage_type = str(user_constraints.get("Storage Type", "")).strip().lower()
    req_cpu = str(user_constraints.get("CPU", "")).strip().lower()
    req_gpu = str(user_constraints.get("GPU", "")).strip().lower()

    cand_name = str(candidate.get("name", ""))
    cand_category = str(candidate.get("category", "")).strip().lower()
    cand_price = int(candidate.get("price", 0) or 0)
    cand_ram = _to_int(candidate.get("RAM", ""))
    cand_storage = _to_int(candidate.get("Storage", ""))
    cand_storage_type = str(candidate.get("Storage Type", "")).strip().lower()
    cand_cpu = str(candidate.get("CPU", "")).strip().lower()
    cand_gpu = str(candidate.get("GPU", "")).strip().lower()

    def _record(field: str, ok: bool, reason: str, required: Any, actual: Any) -> None:
        checks[field] = ok
        if ok:
            matched_reasons.append(reason)
        else:
            mismatches.append(
                {
                    "field": field,
                    "required": required,
                    "actual": actual,
                }
            )

    if req_brand and req_brand != "unknown":
        ok = req_brand in cand_name.lower()
        _record("brand", ok, f"Brand matched ({req_brand.upper()}).", req_brand.upper(), cand_name)

    if req_category and req_category != "unknown":
        ok = req_category in cand_category
        _record("category", ok, f"Category matched ({req_category}).", req_category, cand_category)

    if req_budget > 0:
        ok = cand_price <= req_budget
        _record(
            "price",
            ok,
            f"Within budget ({cand_price} <= {req_budget}).",
            f"<={req_budget}",
            cand_price,
        )

    if req_ram > 0:
        ok = cand_ram >= req_ram
        _record("RAM", ok, f"RAM matched ({cand_ram}GB >= {req_ram}GB).", f">={req_ram}GB", f"{cand_ram}GB")

    if req_storage > 0:
        ok = cand_storage >= req_storage
        _record(
            "Storage",
            ok,
            f"Storage matched ({cand_storage}GB >= {req_storage}GB).",
            f">={req_storage}GB",
            f"{cand_storage}GB",
        )

    if req_storage_type:
        ok = req_storage_type in cand_storage_type
        _record(
            "Storage Type",
            ok,
            f"Storage type matched ({candidate.get('Storage Type', '')}).",
            req_storage_type,
            cand_storage_type,
        )

    if req_cpu:
        ok = req_cpu in cand_cpu
        _record("CPU", ok, f"CPU preference matched ({candidate.get('CPU', '')}).", req_cpu, cand_cpu)

    if req_gpu:
        ok = req_gpu in cand_gpu
        _record("GPU", ok, f"GPU preference matched ({candidate.get('GPU', '')}).", req_gpu, cand_gpu)

    total_checks = len(checks)
    passed_checks = sum(1 for value in checks.values() if value)
    fit_score = int((passed_checks / total_checks) * 100) if total_checks else 100

    if fit_score >= 90:
        fit_status = "perfect_fit"
    elif fit_score >= 75:
        fit_status = "good_fit"
    elif fit_score >= 50:
        fit_status = "partial_fit"
    else:
        fit_status = "no_fit"

    return {
        "fit_score": fit_score,
        "fit_status": fit_status,
        "matched_reasons": matched_reasons,
        "mismatches": mismatches,
        "checks": checks,
    }


def generate_usage_tips_tool(candidate: Dict[str, Any], category: str) -> List[str]:
    """
    Generate practical usage tips for a selected candidate.

    Args:
        candidate: The selected product recommendation.
        category: Normalized user category preference.

    Returns:
        A short list of actionable usage tips.
    """

    tips: List[str] = []
    category_text = str(category or "").lower()
    cpu_text = str(candidate.get("CPU", "")).lower()
    gpu_text = str(candidate.get("GPU", "")).lower()
    ram_gb = _to_int(candidate.get("RAM", ""))
    storage_text = str(candidate.get("Storage Type", "")).lower()

    if category_text == "laptop":
        tips.append("Use performance mode only during heavy tasks to improve battery life.")
        tips.append("Keep air vents clear and clean fans monthly for better thermals.")
    elif category_text == "mobile":
        tips.append("Enable battery protection/optimized charging for longer battery lifespan.")
        tips.append("Use cloud backup for photos and app data before major updates.")
    else:
        tips.append("Apply system and security updates regularly for stable performance.")

    if "rtx" in gpu_text or "gtx" in gpu_text:
        tips.append("Update graphics drivers regularly for game and rendering stability.")
    if ram_gb and ram_gb <= 8:
        tips.append("Limit background apps to keep multitasking smooth on lower RAM.")
    elif ram_gb >= 16:
        tips.append("This memory level supports multitasking; keep startup apps minimal for best responsiveness.")
    if "ssd" in storage_text:
        tips.append("Keep at least 15 percent free SSD space to maintain performance.")
    if "i5" in cpu_text or "ryzen 5" in cpu_text:
        tips.append("Balanced CPU tier is ideal for office work, coding, and light editing.")

    return tips[:5]
