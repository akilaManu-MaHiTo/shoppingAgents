from typing import Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph

from filter_agent import filter_agent
from input_agent import input_agent
from search_agent import search_agent


class ShoppingState(TypedDict, total=False):
    user_input: str
    input_result: Dict[str, Any]
    search_result: Dict[str, Any]
    filter_result: Dict[str, Any]
    error: str


def parse_input_node(state: ShoppingState) -> ShoppingState:
    user_input = str(state.get("user_input", "")).strip()
    if not user_input:
        return {
            "input_result": {},
            "error": "Empty user input.",
        }

    try:
        parsed = input_agent(user_input)
        return {"input_result": parsed}
    except Exception as exc:
        return {
            "input_result": {},
            "error": f"input_agent_failed: {exc}",
        }


def search_products_node(state: ShoppingState) -> ShoppingState:
    if state.get("error"):
        return {}

    spec = state.get("input_result", {})
    if not spec:
        return {
            "search_result": {
                "totalMatches": 0,
                "resultMode": "closest_alternative",
                "searchResults": None,
                "candidates": [],
            }
        }

    try:
        result = search_agent(spec)
        return {"search_result": result}
    except Exception as exc:
        return {
            "search_result": {
                "totalMatches": 0,
                "resultMode": "closest_alternative",
                "searchResults": None,
                "candidates": [],
            },
            "error": f"search_agent_failed: {exc}",
        }


def filter_products_node(state: ShoppingState) -> ShoppingState:
    if state.get("error"):
        return {}

    input_result = state.get("input_result", {})
    search_result = state.get("search_result", {})
    candidates = list(search_result.get("candidates", []) or [])

    if not candidates:
        return {
            "filter_result": {
                "totalFiltered": 0,
                "filterMode": "no_match",
                "filteredResults": None,
                "filteredCandidates": [],
                "filtersApplied": [],
                "filtersSkipped": [],
                "rejectedCount": 0,
                "rejectionLog": [],
                "duplicatesRemoved": 0,
            }
        }

    try:
        result = filter_agent(input_result, search_result)
        return {"filter_result": result}
    except Exception as exc:
        return {
            "filter_result": {
                "totalFiltered": 0,
                "filterMode": "no_match",
                "filteredResults": None,
                "filteredCandidates": [],
                "filtersApplied": [],
                "filtersSkipped": [],
                "rejectedCount": len(candidates),
                "rejectionLog": [],
                "duplicatesRemoved": 0,
            },
            "error": f"filter_agent_failed: {exc}",
        }


def build_shopping_graph():
    graph = StateGraph(ShoppingState)

    graph.add_node("parse_input", parse_input_node)
    graph.add_node("search_products", search_products_node)
    graph.add_node("filter_products", filter_products_node)

    graph.add_edge(START, "parse_input")
    graph.add_edge("parse_input", "search_products")
    graph.add_edge("search_products", "filter_products")
    graph.add_edge("filter_products", END)

    return graph.compile()


def run_shopping_graph(user_input: str) -> ShoppingState:
    app = build_shopping_graph()
    return app.invoke({"user_input": user_input})
