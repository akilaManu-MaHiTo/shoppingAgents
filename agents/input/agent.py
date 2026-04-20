from langchain_ollama import OllamaLLM
import json

from utils.input_tools import (
    clean_json,
    validate_input,
    normalize_category,
    normalize_product_brand,
    extract_price_from_user_input,
    enrich_specs,
    log_input,
    classify_budget,
)
from storage.input_history import get_recent_history, save_history

llm = OllamaLLM(model="llama3")


def input_agent(user_input: str) -> dict:
    """
    Extract structured product specifications from user input
    and enrich them with rule-based logic.
    """

    # Step 1: Load history (state awareness)
    history = get_recent_history()

    # Step 2: Prompt (STRICT, NO HALLUCINATION)
    prompt = f"""
You are a strict product information extraction agent.

Previous Inputs:
{history}

Extract ONLY these fields:

"product","price","category","CPU","Generation","RAM","Storage Type","Storage","GPU"

Rules:
- category must be: laptop or mobile
- product must be ONLY a known brand explicitly mentioned in the user input
- allowed product values are ASUS, MSI, HP, or unknown
- examples:
    - "ASUS TUF Gaming" -> "ASUS"
    - "HP laptop" -> "HP"
    - if the prompt does not mention ASUS/MSI/HP, output "unknown"
- price must be a number
- If missing -> 0 or ""
- DO NOT guess values
- DO NOT invent specs
- If the user explicitly mentions RAM, SSD, storage size, CPU generation, or GPU model, copy those fields exactly
- If the user asks for at least 16GB RAM, 512GB SSD, Intel i5 / Ryzen 5, 11th gen or newer, or RTX 2050 / RTX 3050, extract those hints into the matching fields

STRICT:
- Output ONLY JSON
- No explanation

Format:
{{
"product": "unknown",
"price": 0,
"category": "",
"CPU": "",
"Generation": "",
"RAM": "",
"Storage Type": "",
"Storage": "",
"GPU": ""
}}

User Input:
"{user_input}"
"""

    # Step 3: Call LLM
    response = llm.invoke(prompt)
    print("Raw:", response)

    # Step 4: Clean JSON
    json_text = clean_json(response)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        data = {}

    # Step 5: Normalize category
    data["category"] = normalize_category(data.get("category"), user_input)

    # Step 5.1: Normalize product brand (ASUS/MSI/HP/unknown)
    data["product"] = normalize_product_brand(data.get("product"), user_input)

    # Step 6: Validate base structure
    data = validate_input(data)

    # Step 6.1: Use explicit user price only (ignore LLM hallucinated price)
    user_price = extract_price_from_user_input(user_input)
    data["price"] = user_price

    # Step 7: Enrich specs (rule-based)
    data = enrich_specs(data, user_input)

    # Step 8: Classify budget
    data["budgetType"] = classify_budget(data["price"], user_input)

    # Step 9: Log (observability)
    log_input(data)

    # Step 10: Save to history (state passing)
    save_history(
        {
            "input": user_input,
            "output": data,
            "budgetType": data["budgetType"],
        }
    )

    return data
