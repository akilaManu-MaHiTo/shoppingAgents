from langchain_ollama import OllamaLLM
import json

from input_tools import clean_json, validate_input, normalize_category, log_input
from input_history import get_recent_history, save_history

llm = OllamaLLM(model="llama3")


def input_agent(user_input: str) -> dict:
    """
    Extracts structured product information from user input.

    Args:
        user_input (str): Raw user query

    Returns:
        dict: {"category": str, "budget": int}
    """

    # Step 1: Load recent history
    history = get_recent_history()

    # Step 2: Prompt (STRICT + LOW HALLUCINATION)
    prompt = f"""
You are a strict data extraction agent in a multi-agent system.

Previous Inputs:
{history}

Your task:
Extract ONLY the following fields from the input.

Rules:
- category must be EXACTLY one of: laptop, mobile
- If unclear → "unknown"
- budget must be a number only (no text)
- If missing → 0
- DO NOT guess values
- DO NOT infer beyond what is clearly stated

STRICT OUTPUT RULES:
- Output ONLY valid JSON
- No explanation
- No extra text

Format:
{{"category": "", "budget": 0}}

User Input:
"{user_input}"
"""

    # Step 3: Call LLM
    response = llm.invoke(prompt)
    print("Raw LLM Output:", response)

    # Step 4: Extract JSON safely
    json_text = clean_json(response)

    try:
        data = json.loads(json_text)
    except Exception:
        data = {"category": "unknown", "budget": 0}

    # Step 5: Normalize category
    data["category"] = normalize_category(data.get("category"), user_input)

    # Step 6: Validate data
    data = validate_input(data)

    # Step 7: Log for observability
    log_input(data)

    # Step 8: Save to history (state management)
    save_history({
        "input": user_input,
        "output": data
    })

    return data