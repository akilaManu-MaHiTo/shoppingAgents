import csv
import re
from typing import Dict, List, Tuple


DATASET_PATH = "smart_shopping_dataset.csv"

CATEGORY_MAP = {
    "laptop": "laptop",
    "mobile": "smartphone",
    "smartphone": "smartphone",
    "tv": "television",
    "television": "television",
}


def _to_int(text: str) -> int:
    digits = re.findall(r"\d+", str(text or ""))
    return int(digits[0]) if digits else 0


def _extract_storage_range(storage_text: str) -> Tuple[int, int]:
    """
    Parse storage text like "128GB - 256GB" and return min/max GB.
    If only one number is present, min=max.
    """

    values = [int(v) for v in re.findall(r"\d+", str(storage_text or ""))]
    if not values:
        return 0, 0
    if len(values) == 1:
        return values[0], values[0]
    return min(values), max(values)


def _normalize_storage_gb(storage_value: str) -> int:
    """
    Convert storage string into GB. Handles GB and TB.
    """

    text = str(storage_value or "").upper().replace(" ", "")
    number = _to_int(text)
    if number == 0:
        return 0
    if "TB" in text:
        return number * 1024
    return number


def _brand_match(query_brand: str, product_name: str) -> bool:
    if not query_brand or query_brand.lower() == "unknown":
        return True
    return query_brand.lower() in str(product_name or "").lower()


def _storage_type_match(requested: str, actual: str) -> bool:
    if not requested:
        return True

    requested_l = requested.lower()
    actual_l = str(actual or "").lower()

    if "or" in requested_l:
        # Example: "SSD or HDD" -> accept either.
        tokens = [t.strip() for t in requested_l.split("or")]
        return any(token and token in actual_l for token in tokens)

    return requested_l in actual_l


def _split_requested_variants(text: str) -> List[str]:
    if not text:
        return []

    normalized = re.sub(r"\s+", " ", str(text).strip().lower())
    parts = re.split(r"\s*(?:/|\||,|\bor\b|\band\b)\s*", normalized)
    return [part.strip() for part in parts if part.strip()]


def _normalize_text_token(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def _cpu_tokens(text: str) -> set:
    token_text = _normalize_text_token(text)
    tokens = set()

    if not token_text:
        return tokens

    intel_match = re.search(r"\bi\s*(3|5|7|9)\b", token_text)
    if intel_match:
        tokens.add(f"intel_i{intel_match.group(1)}")

    ryzen_match = re.search(r"\bryzen\s*(3|5|7|9)\b", token_text)
    if ryzen_match:
        tokens.add(f"ryzen_{ryzen_match.group(1)}")

    apple_match = re.search(r"\bapple\s*a\s*(\d+)\b", token_text)
    if apple_match:
        tokens.add(f"apple_a{apple_match.group(1)}")

    snapdragon_match = re.search(r"\bsnapdragon\s*(\d+)\b", token_text)
    if snapdragon_match:
        tokens.add(f"snapdragon_{snapdragon_match.group(1)}")

    dimensity_match = re.search(r"\bdimensity\s*(\d+)\b", token_text)
    if dimensity_match:
        tokens.add(f"dimensity_{dimensity_match.group(1)}")

    if "intel" in token_text and not intel_match:
        tokens.add("intel")
    if "amd" in token_text and not ryzen_match:
        tokens.add("amd")

    return tokens


def _gpu_tokens(text: str) -> set:
    token_text = _normalize_text_token(text)
    tokens = set()

    if not token_text:
        return tokens

    rtx_match = re.search(r"\brtx\s*(\d{4})\b", token_text)
    if rtx_match:
        tokens.add(f"rtx_{rtx_match.group(1)}")

    gtx_match = re.search(r"\bgtx\s*(\d{4})\b", token_text)
    if gtx_match:
        tokens.add(f"gtx_{gtx_match.group(1)}")

    mx_match = re.search(r"\bmx\s*(\d{3})\b", token_text)
    if mx_match:
        tokens.add(f"mx_{mx_match.group(1)}")

    rx_match = re.search(r"\brx\s*(\d{4})\b", token_text)
    if rx_match:
        tokens.add(f"rx_{rx_match.group(1)}")

    if "integrated" in token_text:
        tokens.add("integrated")
    if "adreno" in token_text or "mali" in token_text or "apple gpu" in token_text:
        tokens.add("mobile_gpu")

    return tokens


def _component_match(requested: str, actual: str, component: str) -> bool:
    if not requested:
        return True

    requested_parts = _split_requested_variants(requested)
    actual_text = _normalize_text_token(actual)
    actual_tokens = _cpu_tokens(actual) if component == "cpu" else _gpu_tokens(actual)

    for part in requested_parts:
        req_tokens = _cpu_tokens(part) if component == "cpu" else _gpu_tokens(part)
        req_text = _normalize_text_token(part)

        if req_tokens and actual_tokens and req_tokens.intersection(actual_tokens):
            return True

        if req_text and req_text in actual_text:
            return True

    return False


def load_products(dataset_path: str = DATASET_PATH) -> List[Dict]:
    products: List[Dict] = []

    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["price"] = int(float(row.get("price", 0) or 0))
            row["rating"] = float(row.get("rating", 0) or 0)
            row["RAM_GB"] = _to_int(row.get("RAM", ""))
            row["Storage_GB"] = _normalize_storage_gb(row.get("Storage", ""))
            products.append(row)

    return products


def search_agent(spec: Dict, dataset_path: str = DATASET_PATH, top_n: int = 5) -> Dict:
    """
    Find product candidates from dataset using parsed user spec.

    Returns:
    {
      "totalMatches": int,
            "resultMode": "true_match" | "closest_alternative",
            "searchResults": {...} or None,
      "candidates": [...]
    }
    """

    products = load_products(dataset_path)

    req_brand = str(spec.get("product", "unknown"))
    req_category = CATEGORY_MAP.get(str(spec.get("category", "")).strip().lower(), "")
    req_ram_gb = _to_int(spec.get("RAM", ""))
    req_storage_min, req_storage_max = _extract_storage_range(spec.get("Storage", ""))
    req_storage_type = str(spec.get("Storage Type", "")).strip()
    req_gpu = str(spec.get("GPU", "")).strip().lower()
    req_cpu = str(spec.get("CPU", "")).strip().lower()
    req_budget = int(spec.get("price", 0) or 0)
    budget_type = str(spec.get("budgetType", "")).lower()

    # Guard against accidental price from RAM text (e.g., 8 from "8GB RAM").
    if 0 < req_budget < 100:
        req_budget = 0

    def _collect_candidates(relaxed_level: int = 0) -> List[Dict]:
        candidates: List[Dict] = []
        for item in products:
            item_category = str(item.get("category", "")).strip().lower()
            if req_category and item_category != req_category:
                continue

            if not _brand_match(req_brand, item.get("name", "")):
                continue

            if relaxed_level == 0:
                ram_floor = req_ram_gb
            elif relaxed_level == 1:
                ram_floor = max(0, req_ram_gb - 4)
            else:
                ram_floor = 0
            if ram_floor and item.get("RAM_GB", 0) < ram_floor:
                continue

            storage_gb = item.get("Storage_GB", 0)
            if relaxed_level == 0:
                storage_min = req_storage_min
                storage_max = req_storage_max
            elif relaxed_level == 1:
                storage_min = int(req_storage_min * 0.8)
                storage_max = int(req_storage_max * 1.2) if req_storage_max else req_storage_max
            else:
                storage_min = 0
                storage_max = 0

            if storage_min and storage_gb < storage_min:
                continue
            if storage_max and storage_gb > storage_max:
                continue

            if relaxed_level == 0 and req_storage_type and not _storage_type_match(req_storage_type, item.get("Storage Type", "")):
                continue

            if req_gpu and not _component_match(req_gpu, item.get("GPU", ""), "gpu"):
                if relaxed_level == 0:
                    continue

            if req_cpu and not _component_match(req_cpu, item.get("CPU", ""), "cpu"):
                if relaxed_level == 0:
                    continue

            if relaxed_level == 0:
                effective_budget = req_budget
            elif relaxed_level == 1:
                effective_budget = int(req_budget * 1.1)
            else:
                effective_budget = int(req_budget * 1.25)
            if effective_budget and item.get("price", 0) > effective_budget:
                continue

            scored_item = dict(item)
            # Higher rating is better; lower price is better.
            # New dataset prices are much larger, so keep price penalty lighter.
            scored_item["_score"] = item.get("rating", 0) * 100 - item.get("price", 0) * 0.001
            if relaxed_level > 0:
                # Keep strict matches ahead when both are present.
                scored_item["_score"] -= 5 * relaxed_level
            candidates.append(scored_item)

        return candidates

    used_relaxed_level = 0
    candidates = _collect_candidates(relaxed_level=0)

    # No-result fallback: relax a few strict constraints to return useful alternatives.
    if not candidates:
        used_relaxed_level = 1
        candidates = _collect_candidates(relaxed_level=1)
    if not candidates:
        used_relaxed_level = 2
        candidates = _collect_candidates(relaxed_level=2)

    if not req_budget and budget_type in {"low", "mid", "high"} and candidates:
        candidates_sorted_by_price = sorted(candidates, key=lambda x: x["price"])
        chunk = max(1, len(candidates_sorted_by_price) // 3)
        if budget_type == "low":
            candidates = candidates_sorted_by_price[:chunk]
        elif budget_type == "mid":
            candidates = candidates_sorted_by_price[chunk : chunk * 2]
        else:
            candidates = candidates_sorted_by_price[chunk * 2 :]

    ranked = sorted(candidates, key=lambda x: (x["_score"], x["rating"]), reverse=True)

    response_candidates = []
    result_mode = "true_match" if used_relaxed_level == 0 else "closest_alternative"
    for row in ranked[:top_n]:
        response_candidates.append(
            {
                "name": row["name"],
                "category": row.get("category", ""),
                "price": row["price"],
                "rating": row["rating"],
                "RAM": row["RAM"],
                "Storage": row["Storage"],
                "Storage Type": row["Storage Type"],
                "CPU": row["CPU"],
                "GPU": row["GPU"],
                "StoreName": row.get("StoreName", ""),
                "Location": row.get("Location", ""),
                "matchType": result_mode,
                "relaxationLevel": used_relaxed_level,
            }
        )

    return {
        "totalMatches": len(ranked),
        "resultMode": result_mode,
        "searchResults": response_candidates[0] if response_candidates else None,
        "candidates": response_candidates,
    }