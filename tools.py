import re
from typing import Dict


def clean_json(text: str) -> str:
    """
    Extract the first JSON object from LLM output.

    Args:
        text (str): Raw LLM response

    Returns:
        str: Extracted JSON string or "{}" if not found
    """
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    return match.group(0) if match else "{}"


def validate_input(data: Dict) -> Dict:
    """
    Validate and enforce constraints on extracted data.

    Args:
        data (Dict): Extracted JSON data

    Returns:
        Dict: Cleaned and validated data
    """

    # Validate category
    if data.get("category") not in {"laptop", "mobile"}:
        data["category"] = "unknown"

    # Validate budget
    try:
        budget = int(data.get("budget", 0))
        if budget < 0:
            budget = 0
    except (ValueError, TypeError):
        budget = 0

    data["budget"] = budget

    return data


def normalize_category(category: str, user_input: str = "") -> str:
    """
    Normalize category using simple keyword matching.

    Args:
        category (str): Model output category
        user_input (str): Original user input

    Returns:
        str: Normalized category (laptop/mobile/unknown)
    """

    if not category:
        category = ""

    category = category.lower().strip()
    user_input = user_input.lower().strip()

    # Direct match
    if category in {"laptop", "mobile"}:
        return category

    # Keyword-based fallback (SAFE inference)
    if any(word in user_input for word in ["laptop", "notebook", "pc"]):
        return "laptop"

    if any(word in user_input for word in ["phone", "mobile", "smartphone", "iphone", "android"]):
        return "mobile"

    return "unknown"


def log_input(data: Dict) -> None:
    """
    Log agent output for observability.

    Args:
        data (Dict): Final processed data
    """
    with open("agent_log.txt", "a") as f:
        f.write(str(data) + "\n")