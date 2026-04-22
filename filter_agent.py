import re
from typing import Any, Dict, List, Tuple

from search_agent import (
	CATEGORY_MAP,
	_brand_match,
	_component_match,
	_normalize_storage_gb,
	_storage_type_match,
	_to_int,
)


MIN_RATING_DEFAULT = 3.5

FIELD_WEIGHTS = {
	"GPU": 30,
	"CPU": 20,
	"price": 20,
	"RAM": 15,
	"Storage": 15,
	"Generation": 10,
	"brand": 10,
	"category": 10,
	"Storage Type": 8,
	"rating": 6,
	"StoreName": 6,
	"Location": 6,
}


def _safe_float(value: Any) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return 0.0


def _normalize_category(value: str) -> str:
	return CATEGORY_MAP.get(str(value or "").strip().lower(), str(value or "").strip().lower())


def _generation_match(requested: str, actual: str) -> bool:
	if not requested:
		return True
	return str(requested).strip().lower() in str(actual or "").strip().lower()


def _split_variants(text: str) -> List[str]:
	parts = re.split(r"\s*(?:/|\||,|\bor\b|\band\b)\s*", str(text or "").strip(), flags=re.IGNORECASE)
	return [p.strip() for p in parts if p.strip()]


def _cpu_tier(text: str) -> Tuple[str, int]:
	t = str(text or "").lower()
	intel = re.search(r"\bintel\s*i\s*(3|5|7|9)\b|\bi\s*(3|5|7|9)\b", t)
	if intel:
		value = intel.group(1) or intel.group(2)
		return "intel", int(value)

	ryzen = re.search(r"\b(?:amd\s*)?ryzen\s*(3|5|7|9)\b", t)
	if ryzen:
		return "ryzen", int(ryzen.group(1))

	return "", 0


def _cpu_match(requested: str, actual: str, strict: bool = False) -> bool:
	if not requested:
		return True

	if strict:
		return _component_match(requested, actual, "cpu")

	for variant in _split_variants(requested):
		if _component_match(variant, actual, "cpu"):
			return True

		req_vendor, req_tier = _cpu_tier(variant)
		act_vendor, act_tier = _cpu_tier(actual)
		if req_vendor and act_vendor and req_vendor == act_vendor and req_tier and act_tier >= req_tier:
			return True

	return False


def _generation_min_match(requested: str, actual: str, strict: bool = False) -> bool:
	if not requested:
		return True

	if strict:
		return _generation_match(requested, actual)

	req_num = _to_int(requested)
	act_num = _to_int(actual)
	if req_num and act_num:
		return act_num >= req_num

	return _generation_match(requested, actual)


def _gpu_tier_value(text: str) -> int:
	t = str(text or "").lower()
	rtx = re.search(r"\brtx\s*(\d{4})\b", t)
	if rtx:
		return 30000 + int(rtx.group(1))

	gtx = re.search(r"\bgtx\s*(\d{4})\b", t)
	if gtx:
		return 20000 + int(gtx.group(1))

	rx = re.search(r"\brx\s*(\d{4})\b", t)
	if rx:
		return 21000 + int(rx.group(1))

	mx = re.search(r"\bmx\s*(\d{3})\b", t)
	if mx:
		return 10000 + int(mx.group(1))

	if "integrated" in t:
		return 1000

	return 0


def _gpu_match_with_tier(requested: str, actual: str, strict: bool = False) -> bool:
	if not requested:
		return True

	if strict:
		return _component_match(requested, actual, "gpu")

	for variant in _split_variants(requested):
		if _component_match(variant, actual, "gpu"):
			return True

		req_tier = _gpu_tier_value(variant)
		act_tier = _gpu_tier_value(actual)
		if req_tier and act_tier and act_tier >= req_tier:
			return True

	return False


def _is_user_explicit(field: str, input_result: Dict[str, Any]) -> bool:
	"""
	Check if a field is explicitly provided by user (in explicitConstraints).
	Only fields in explicitConstraints are truly user-provided.
	This is more reliable than pattern-based inference.
	"""
	explicit = input_result.get("explicitConstraints", {})
	if isinstance(explicit, dict) and field in explicit:
		return True
	return False


def _build_filter_spec(input_result: Dict[str, Any]) -> Tuple[List[Tuple[str, Any]], List[str], List[str]]:
	explicit = input_result.get("explicitConstraints", {})
	use_explicit = isinstance(explicit, dict) and bool(explicit)

	def _pick(key: str, default: Any = "") -> Any:
		if use_explicit:
			return explicit.get(key, default)
		return input_result.get(key, default)

	# FIX: Properly resolve strict_filters from BOTH sources
	strict_filters = set()
	if isinstance(explicit, dict):
		strict_filters = set(str(v).lower() for v in (explicit.get("strictFilters", []) or []))
	if not strict_filters:
		strict_filters = set(str(v).lower() for v in (input_result.get("strictFilters", []) or []))

	# FIX: Get intent mode from input (determines soft vs strict globally)
	intent_mode = str(input_result.get("intentMode", "normal")).lower()

	active_filters: List[Tuple[str, Any]] = []
	filters_applied: List[str] = []
	filters_skipped: List[str] = []
	has_user_criteria = False

	brand = str(_pick("product", "")).strip()
	if brand and brand.lower() != "unknown":
		active_filters.append(("brand", {"value": brand, "strict": False, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"brand:{brand}")
		has_user_criteria = True
	else:
		filters_skipped.append("brand")

	budget = int(_pick("price", 0) or 0)
	if budget > 0:
		active_filters.append(("price", {"value": budget, "strict": False, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"price:\u2264{budget}")
		has_user_criteria = True
	else:
		filters_skipped.append("price")

	category = _normalize_category(_pick("category", ""))
	if category and category != "unknown":
		active_filters.append(("category", {"value": category, "strict": False, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"category:{category}")
		has_user_criteria = True
	else:
		filters_skipped.append("category")

	ram_gb = _to_int(_pick("RAM", ""))
	if ram_gb > 0:
		active_filters.append(("RAM", {"value": ram_gb, "strict": False, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"RAM:\u2265{ram_gb}GB")
		has_user_criteria = True
	else:
		filters_skipped.append("RAM")

	# FIX: Use _is_user_explicit() instead of pattern-based inference
	is_storage_explicit = _is_user_explicit("Storage", input_result)
	storage_gb = _normalize_storage_gb(_pick("Storage", ""))
	if storage_gb > 0 and is_storage_explicit:
		active_filters.append(("Storage", {"value": storage_gb, "strict": False, "source": "explicit"}))
		filters_applied.append(f"Storage:\u2265{storage_gb}GB")
		has_user_criteria = True
	else:
		filters_skipped.append("Storage")

	is_storage_type_explicit = _is_user_explicit("Storage Type", input_result)
	storage_type = str(_pick("Storage Type", "")).strip()
	if storage_type and is_storage_type_explicit:
		active_filters.append(("Storage Type", {"value": storage_type, "strict": False, "source": "explicit"}))
		filters_applied.append(f"Storage Type:{storage_type}")
		has_user_criteria = True
	else:
		filters_skipped.append("Storage Type")

	# FIX: Check strict_filters properly (case-insensitive)
	gpu = str(_pick("GPU", "")).strip()
	if gpu:
		is_strict_gpu = "gpu" in strict_filters or intent_mode == "strict"
		active_filters.append(("GPU", {"value": gpu, "strict": is_strict_gpu, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"GPU:{gpu}")
		has_user_criteria = True
	else:
		filters_skipped.append("GPU")

	cpu = str(_pick("CPU", "")).strip()
	if cpu:
		is_strict_cpu = "cpu" in strict_filters or intent_mode == "strict"
		active_filters.append(("CPU", {"value": cpu, "strict": is_strict_cpu, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"CPU:{cpu}")
		has_user_criteria = True
	else:
		filters_skipped.append("CPU")

	generation = str(_pick("Generation", "")).strip()
	if generation:
		is_strict_gen = "generation" in strict_filters or intent_mode == "strict"
		active_filters.append(("Generation", {"value": generation, "strict": is_strict_gen, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"Generation:{generation}")
		has_user_criteria = True
	else:
		filters_skipped.append("Generation")

	has_explicit_rating = str(_pick("minRating", "")).strip() != ""
	min_rating = _safe_float(_pick("minRating", MIN_RATING_DEFAULT) or MIN_RATING_DEFAULT)
	if min_rating > 0 and (has_explicit_rating or has_user_criteria):
		source = "explicit" if has_explicit_rating else "default"
		active_filters.append(("rating", {"value": min_rating, "strict": False, "source": source}))
		if source == "default":
			filters_applied.append(f"rating(default):\u2265{min_rating}")
		else:
			filters_applied.append(f"rating:\u2265{min_rating}")
	else:
		filters_skipped.append("rating")

	store_name = str(_pick("StoreName", "")).strip()
	if store_name:
		active_filters.append(("StoreName", {"value": store_name, "strict": False, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"StoreName:{store_name}")
		has_user_criteria = True
	else:
		filters_skipped.append("StoreName")

	location = str(_pick("Location", "")).strip()
	if location:
		active_filters.append(("Location", {"value": location, "strict": False, "source": "explicit" if use_explicit else "input"}))
		filters_applied.append(f"Location:{location}")
		has_user_criteria = True
	else:
		filters_skipped.append("Location")

	return active_filters, filters_applied, filters_skipped


def _dedupe_candidates(candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
	grouped: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {}
	original_count = len(candidates)

	for item in candidates:
		key = (
			str(item.get("name", "")).strip().lower(),
			str(item.get("RAM", "")).strip().lower(),
			str(item.get("Storage", "")).strip().lower(),
			str(item.get("GPU", "")).strip().lower(),
			str(item.get("CPU", "")).strip().lower(),
		)

		existing = grouped.get(key)
		if not existing or int(item.get("price", 0) or 0) < int(existing.get("price", 0) or 0):
			grouped[key] = item

	deduped = list(grouped.values())
	duplicates_removed = original_count - len(deduped)
	return deduped, duplicates_removed


def filter_agent(input_result: Dict[str, Any], search_result: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Deterministic filtering engine for product candidates.
	
	FILTER CONTRACT (Input Requirements):
	- input_result MUST contain:
	  * explicitConstraints: Dict with user-provided fields (source of truth for explicit vs inferred)
	  * Optional: intentMode ("normal" | "strict") for soft vs strict matching
	  * Optional: strictFilters list for per-field strict control
	
	- search_result MUST contain:
	  * candidates: List of Dict with fields [name, price, category, RAM, Storage, GPU, CPU, Generation, rating, StoreName, Location, Storage Type]
	
	FILTER CONTRACT (Output Guarantee):
	- Always returns Dict with:
	  * filterMode: "exact_filter" | "near_match" | "no_match"
	  * totalFiltered: int (number of matching candidates)
	  * filteredCandidates: List[Dict] (candidates that passed filters)
	  * filtersApplied: List[str] (active filters used)
	  * filtersSkipped: List[str] (filters not applied)
	  * rejectionLog: List[Dict] (detailed rejection reasons)
	  * duplicatesRemoved: int (deduplication count)
	
	IMPLICIT DEPENDENCIES (DO NOT BREAK):
	- Relies on search_agent._component_match for GPU/CPU matching
	- Assumes candidates enriched with category field from search_agent
	- Assumes input_result from parse_input/input_agent pipeline
	
	DEBUG SNAPSHOT (for troubleshooting):
	- Check filter_debug_snapshot in returned Dict for:
	  * input_fields: user input summary
	  * active_filters_count: number of active filters
	  * candidates_received: total candidates before filtering
	  * final_mode: which filtering mode was triggered
	"""
	candidates = list(search_result.get("candidates", []) or [])
	active_filters, filters_applied, filters_skipped = _build_filter_spec(input_result)

	filtered: List[Dict[str, Any]] = []
	rejection_log: List[Dict[str, Any]] = []
	near_match_pool: List[Dict[str, Any]] = []

	total_active = len(active_filters)

	for candidate in candidates:
		rejected_by: List[str] = []
		details: Dict[str, Dict[str, Any]] = {}
		matched_fields = 0
		matched_weight = 0
		total_weight = 0
		inferred_penalty = 0

		for filter_name, rule in active_filters:
			required = rule.get("value") if isinstance(rule, dict) else rule
			strict = bool(rule.get("strict", False)) if isinstance(rule, dict) else False
			source = str(rule.get("source", "input")) if isinstance(rule, dict) else "input"
			weight = int(FIELD_WEIGHTS.get(filter_name, 10))
			total_weight += weight
			# FIX: Make penalty proportional to field weight
			if source == "default":
				inferred_penalty += weight * 0.15

			if filter_name == "brand":
				ok = _brand_match(str(required), candidate.get("name", ""))
				actual = candidate.get("name", "")
				required_desc = required
			elif filter_name == "price":
				actual_price = int(candidate.get("price", 0) or 0)
				ok = actual_price <= int(required)
				actual = actual_price
				required_desc = f"<={required}"
			elif filter_name == "category":
				actual_category = _normalize_category(candidate.get("category", ""))
				ok = actual_category == str(required)
				actual = actual_category
				required_desc = required
			elif filter_name == "RAM":
				actual_ram = _to_int(candidate.get("RAM", ""))
				ok = actual_ram >= int(required)
				actual = actual_ram
				required_desc = f">={required}GB"
			elif filter_name == "Storage":
				actual_storage = _normalize_storage_gb(candidate.get("Storage", ""))
				ok = actual_storage >= int(required)
				actual = actual_storage
				required_desc = f">={required}GB"
			elif filter_name == "Storage Type":
				actual_storage_type = str(candidate.get("Storage Type", ""))
				ok = _storage_type_match(str(required), actual_storage_type)
				actual = actual_storage_type
				required_desc = required
			elif filter_name == "GPU":
				actual_gpu = str(candidate.get("GPU", ""))
				ok = _gpu_match_with_tier(str(required), actual_gpu, strict=strict)
				actual = actual_gpu
				required_desc = required
			elif filter_name == "CPU":
				actual_cpu = str(candidate.get("CPU", ""))
				ok = _cpu_match(str(required), actual_cpu, strict=strict)
				actual = actual_cpu
				required_desc = required
			elif filter_name == "Generation":
				actual_generation = str(candidate.get("Generation", candidate.get("CPU", "")))
				ok = _generation_min_match(str(required), actual_generation, strict=strict)
				actual = actual_generation
				required_desc = required
			elif filter_name == "rating":
				actual_rating = _safe_float(candidate.get("rating", 0))
				ok = actual_rating >= float(required)
				actual = actual_rating
				required_desc = f">={required}"
			elif filter_name == "StoreName":
				actual_store = str(candidate.get("StoreName", "")).strip().lower()
				ok = str(required).strip().lower() == actual_store
				actual = candidate.get("StoreName", "")
				required_desc = required
			elif filter_name == "Location":
				actual_location = str(candidate.get("Location", "")).strip().lower()
				ok = str(required).strip().lower() == actual_location
				actual = candidate.get("Location", "")
				required_desc = required
			else:
				ok = True
				actual = ""
				required_desc = required

			if ok:
				matched_fields += 1
				matched_weight += weight
			else:
				rejected_by.append(filter_name)
				details[filter_name] = {
					"required": required_desc,
					"actual": actual,
				}

		weighted_match = (matched_weight / total_weight) * 100 if total_weight else 100.0
		weighted_match = max(0.0, min(100.0, weighted_match - inferred_penalty))

		near_candidate = dict(candidate)
		near_candidate["matchPercentage"] = round(weighted_match, 2)
		near_candidate["failedFilters"] = rejected_by
		near_candidate["_score"] = _safe_float(candidate.get("rating", 0)) * 100 - int(candidate.get("price", 0) or 0) * 0.001
		near_match_pool.append(near_candidate)

		if rejected_by:
			rejection_log.append(
				{
					"candidateName": candidate.get("name", ""),
					"rejectedBy": rejected_by,
					"details": details,
				}
			)
			continue

		enriched_candidate = dict(candidate)
		enriched_candidate["matchPercentage"] = round(weighted_match, 2) if total_active else 100.0
		enriched_candidate["_score"] = _safe_float(candidate.get("rating", 0)) * 100 - int(candidate.get("price", 0) or 0) * 0.001
		filtered.append(enriched_candidate)

	deduped, duplicates_removed = _dedupe_candidates(filtered)
	ranked = sorted(
		deduped,
		key=lambda row: (
			float(row.get("_score", 0) or 0),
			_safe_float(row.get("rating", 0)),
			-int(row.get("price", 0) or 0),
		),
		reverse=True,
	)

	clean_candidates: List[Dict[str, Any]] = []
	for item in ranked:
		row = dict(item)
		row.pop("_score", None)
		clean_candidates.append(row)

	# Build debug snapshot for production monitoring/troubleshooting
	debug_snapshot = {
		"input_fields": {
			"product": str(input_result.get("product", "")).strip() or "any",
			"price": input_result.get("price", 0),
			"category": str(input_result.get("category", "")).strip() or "any",
			"has_explicit_constraints": bool(input_result.get("explicitConstraints")),
			"intent_mode": input_result.get("intentMode", "normal"),
		},
		"active_filters_count": len(active_filters),
		"candidates_received": len(candidates),
		"rejection_reasons_total": len(rejection_log),
	}

	# FIX: Improved near_match fallback - trigger when very few exact matches too
	if len(clean_candidates) == 0:
		near_candidates = [c for c in near_match_pool if float(c.get("matchPercentage", 0) or 0) >= 60.0]
		near_candidates = sorted(
			near_candidates,
			key=lambda row: (
				float(row.get("matchPercentage", 0) or 0),
				float(row.get("_score", 0) or 0),
			),
			reverse=True,
		)
		clean_near: List[Dict[str, Any]] = []
		for item in near_candidates:
			row = dict(item)
			row.pop("_score", None)
			clean_near.append(row)

		if clean_near:
			debug_snapshot["final_mode"] = "near_match"
			return {
				"totalFiltered": len(clean_near),
				"filterMode": "near_match",
				"message": "No exact matches, showing closest alternatives.",
				"filteredResults": clean_near[0],
				"filteredCandidates": clean_near,
				"filtersApplied": filters_applied,
				"filtersSkipped": filters_skipped,
				"rejectedCount": len(rejection_log),
				"rejectionLog": rejection_log,
				"duplicatesRemoved": 0,
				"filter_debug_snapshot": debug_snapshot,
			}

	debug_snapshot["final_mode"] = "exact_filter" if clean_candidates else "no_match"
	return {
		"totalFiltered": len(clean_candidates),
		"filterMode": "exact_filter" if clean_candidates else "no_match",
		"message": "" if clean_candidates else "No products match all your criteria.",
		"filteredResults": clean_candidates[0] if clean_candidates else None,
		"filteredCandidates": clean_candidates,
		"filtersApplied": filters_applied,
		"filtersSkipped": filters_skipped,
		"rejectedCount": len(rejection_log),
		"rejectionLog": rejection_log,
		"duplicatesRemoved": duplicates_removed,
		"filter_debug_snapshot": debug_snapshot,
	}
