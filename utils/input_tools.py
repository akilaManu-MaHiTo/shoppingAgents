import re
import json
from pathlib import Path
from typing import Dict


KNOWN_BRANDS = {"ASUS", "MSI", "HP"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = PROJECT_ROOT / "agent_log.txt"


def _extract_brand_from_input(user_input: str) -> str:
    """
    Return a known brand mentioned in the user prompt.
    """

    text = str(user_input or "").upper()
    for brand in KNOWN_BRANDS:
        if brand in text:
            return brand

    return "unknown"


def _is_missing_value(value) -> bool:
    """
    Treat blank and placeholder values as missing.
    """

    if value is None:
        return True

    text = str(value).strip().lower()
    return text in {"", "unknown", "null", "none"}


def extract_price_from_user_input(user_input: str) -> int:
    """
    Extract an explicit numeric price from user input.
    Returns 0 when no numeric price is provided.
    """

    text = str(user_input or "")
    numbers = re.findall(r"\d[\d,]*", text)
    if not numbers:
        return 0

    try:
        return int(numbers[0].replace(",", ""))
    except (ValueError, TypeError):
        return 0


def normalize_product_brand(product: str, user_input: str = "") -> str:
    """
    Prefer an explicit brand from the user prompt and otherwise keep only a
    known brand returned by the model.
    """

    brand_from_input = _extract_brand_from_input(user_input)
    if brand_from_input != "unknown":
        return brand_from_input

    if not _is_missing_value(product):
        candidate = str(product).strip().upper()
        if candidate in KNOWN_BRANDS:
            return candidate

    return "unknown"


def clean_json(text: str) -> str:
    """
    Extract and fix JSON (removes duplicates safely).
    """
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        return "{}"

    json_text = match.group(0)

    try:
        parsed = json.loads(json_text)
        return json.dumps(parsed)
    except json.JSONDecodeError:
        return "{}"


def validate_input(data: Dict) -> Dict:
    """
    Ensure required fields exist with safe defaults and valid types.
    """

    schema = {
        "product": "unknown",
        "price": 0,
        "category": "unknown",
        "CPU": "",
        "Generation": "",
        "RAM": "",
        "Storage Type": "",
        "Storage": "",
        "GPU": "",
    }

    for key, default in schema.items():
        data[key] = data.get(key, default)

    # Numeric cleaning
    try:
        data["price"] = int(str(data.get("price", 0)).replace(",", ""))
    except (ValueError, TypeError):
        data["price"] = 0

    return data


def normalize_category(category: str, user_input: str = "") -> str:
    """
    Normalize category using input + LLM output.
    """

    text = f"{category or ''} {user_input or ''}".lower()

    if any(w in text for w in ["laptop", "notebook", "pc"]):
        return "laptop"

    if any(w in text for w in ["phone", "mobile", "iphone", "android"]):
        return "mobile"

    return "unknown"


def normalize_specs(data: Dict) -> Dict:
    """
    Normalize RAM and Storage formats.
    """

    if data["RAM"]:
        data["RAM"] = data["RAM"].upper().replace(" ", "")
        if "GB" not in data["RAM"]:
            data["RAM"] += "GB"

    if data["Storage"]:
        data["Storage"] = data["Storage"].upper().replace(" ", "")
        if not any(x in data["Storage"] for x in ["GB", "TB"]):
            data["Storage"] += "GB"

    # LLM sometimes returns 0/0GB/0TB for unknown storage; normalize as missing.
    if str(data.get("Storage", "")).upper().replace(" ", "") in {"0", "0GB", "0TB"}:
        data["Storage"] = ""

    return data


def enrich_specs(data: Dict, user_input: str) -> Dict:
    """
    Rule-based enrichment (NO hallucination).
    """

    text = user_input.lower()
    price = data.get("price", 0)

    brand_from_input = _extract_brand_from_input(user_input)
    if brand_from_input != "unknown":
        data["product"] = brand_from_input

    # Explicit CPU / generation preferences.
    if re.search(r"(intel\s*)?i5|ryzen\s*5", text):
        data["CPU"] = "Intel i5 / Ryzen 5"

    generation_match = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s*gen(?:eration)?", text)
    if generation_match:
        data["Generation"] = f"{generation_match.group(1)}th Gen"

    if re.search(r"11th\s*gen(?:eration)?\s*(?:or\s*newer)?", text):
        data["Generation"] = "11th Gen+"

    # Explicit memory and storage constraints.
    ram_match = re.search(r"(?:at\s*least|min(?:imum)?|>=?)\s*(\d+)\s*gb\s*ram", text)
    if ram_match:
        data["RAM"] = f"{ram_match.group(1)}GB"

    if not data["RAM"]:
        simple_ram_match = re.search(r"\b(\d+)\s*gb\s*ram\b", text)
        if simple_ram_match:
            data["RAM"] = f"{simple_ram_match.group(1)}GB"

    storage_match = re.search(
        r"(?:storage|ssd|nvme)[^\d]{0,25}(\d+)\s*gb(?:\s*or\s*higher|\+)?",
        text,
    )
    if storage_match:
        data["Storage"] = f"{storage_match.group(1)}GB"

    # Dedicated GPU requests should be preserved when explicit.
    gpu_match = re.search(r"\b(rtx\s*\d{4}|gtx\s*\d{4}|radeon\s*rx\s*\d{4}|mx\s*\d{3})\b", text)
    if gpu_match:
        data["GPU"] = gpu_match.group(1).upper().replace("  ", " ")

    # USER PREFERENCES (explicit constraints)
    if "ssd" in text:
        data["Storage Type"] = "SSD"
    elif "hdd" in text:
        data["Storage Type"] = "HDD"
    elif "nvme" in text:
        data["Storage Type"] = "NVMe SSD"

    if any(token in text for token in ["decent processor", "general use", "everyday use", "office use"]):
        if not data["CPU"]:
            data["CPU"] = "Intel i5 / Ryzen 5"

    # HIGH-END
    if ("high end" in text or "high-end" in text) and data["category"] == "laptop":

        # Enforce high-end mapping by your threshold rule (> 400000).
        data["RAM"] = "32GB" if price > 400000 else "16GB"
        data["GPU"] = "RTX 4060" if price > 400000 else "RTX 3050"

        if not data["CPU"]:
            data["CPU"] = "Intel i7 / Ryzen 7"

    # GAMING
    if "gaming" in text and data["category"] == "laptop":

        if not data["RAM"]:
            data["RAM"] = "16GB"

        if not data["GPU"]:
            if price > 400000:
                data["GPU"] = "RTX 4060"
            elif price >= 150000:
                data["GPU"] = "RTX 3050"
            else:
                data["GPU"] = "GTX 1650"

        if not data["CPU"]:
            data["CPU"] = "Intel i5 / Ryzen 5"

    # LOW BUDGET
    if ("cheap" in text or "budget" in text) and data["price"] == 0:
        data["price"] = 100000

    # Normalize first so invalid storage like 0GB is converted to empty,
    # then apply defaults on the cleaned values.
    data = normalize_specs(data)

    # DEFAULT STORAGE
    if not data["Storage"]:
        data["Storage"] = "512GB"

    if not data["Storage Type"]:
        data["Storage Type"] = "SSD"

    return data


def classify_budget(price: int, user_input: str) -> str:
    """
    Classify budget type using price first, then keywords.
    """

    text = user_input.lower()

    # PRIORITY 1: Use price if available
    if price > 0:
        if price <= 100000:
            return "low"
        if price <= 400000:
            return "mid"
        return "high"

    # PRIORITY 2: Use keywords only if price is missing
    if "cheap" in text or "budget" in text:
        return "low"

    if "mid" in text:
        return "mid"

    if "high end" in text or "premium" in text:
        return "high"

    return "unknown"


def log_input(data: Dict) -> None:
    """
    Log outputs for observability.
    """
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except IOError:
        print("Logging failed")
