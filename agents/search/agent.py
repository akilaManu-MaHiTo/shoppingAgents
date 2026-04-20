import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple


DATASET_PATH = Path(__file__).resolve().parents[2] / "smart_shopping_dataset.csv"

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


def load_products(dataset_path: Path = DATASET_PATH) -> List[Dict]:
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


def search_agent(spec: Dict, dataset_path: Path = DATASET_PATH, top_n: int = 5) -> Dict:
    """
    Find product candidates from dataset using parsed user spec.

    Returns:
    {
      "totalMatches": int,
      "bestOption": {...} or None,
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

    candidates: List[Dict] = []
    for item in products:
        item_category = str(item.get("category", "")).strip().lower()
        if req_category and item_category != req_category:
            continue

        if not _brand_match(req_brand, item.get("name", "")):
            continue

        if req_ram_gb and item.get("RAM_GB", 0) < req_ram_gb:
            continue

        storage_gb = item.get("Storage_GB", 0)
        if req_storage_min and storage_gb < req_storage_min:
            continue
        if req_storage_max and storage_gb > req_storage_max:
            continue

        if req_storage_type and not _storage_type_match(req_storage_type, item.get("Storage Type", "")):
            continue

        if req_gpu and req_gpu not in str(item.get("GPU", "")).lower():
            continue

        if req_cpu and req_cpu not in str(item.get("CPU", "")).lower():
            continue

        if req_budget and item.get("price", 0) > req_budget:
            continue

        scored_item = dict(item)
        # Higher rating is better; lower price is better.
        # New dataset prices are much larger, so keep price penalty lighter.
        scored_item["_score"] = item.get("rating", 0) * 100 - item.get("price", 0) * 0.001
        candidates.append(scored_item)

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
    for row in ranked[:top_n]:
        response_candidates.append(
            {
                "name": row["name"],
                "price": row["price"],
                "rating": row["rating"],
                "RAM": row["RAM"],
                "Storage": row["Storage"],
                "Storage Type": row["Storage Type"],
                "CPU": row["CPU"],
                "GPU": row["GPU"],
                "StoreName": row.get("StoreName", ""),
                "Location": row.get("Location", ""),
            }
        )

    return {
        "totalMatches": len(ranked),
        "bestOption": response_candidates[0] if response_candidates else None,
        "candidates": response_candidates,
    }
