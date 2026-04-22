# Shopping Agents

Multi-agent shopping assistant pipeline that parses user intent, searches a local product dataset, and applies deterministic post-search filtering.

## Latest System State

The system now runs a 3-node LangGraph flow:

1. Input Agent: parse and normalize user request
2. Search Agent: find candidates with strict + relaxed search fallback
3. Filter Agent: deterministic filtering, deduplication, scoring, and rejection logging

The filter layer has been stabilized and instrumented with a per-request debug snapshot for faster production troubleshooting.

## Architecture

- main.py: CLI entrypoint
- langgraph_flow.py: graph orchestration and state flow
- input_agent.py: LLM + rule extraction
- input_tools.py: normalization, enrichment, and validation helpers
- search_agent.py: dataset search and initial candidate generation
- filter_agent.py: deterministic post-search filtering and ranking
- input_history.py: input history persistence helpers
- smart_shopping_dataset.csv: local product dataset
- input_history.json: saved context for input processing
- agent_log.txt: append-only operational log

## End-to-End Flow

1. User enters query in CLI
2. run_shopping_graph(user_input) executes:
   - parse_input_node -> input_result
   - search_products_node -> search_result
   - filter_products_node -> filter_result
3. CLI prints input/search/filter outputs and summary

## Filter Agent Highlights

filter_agent.py provides deterministic filtering across:

- brand
- price
- category
- RAM
- Storage
- Storage Type
- GPU
- CPU
- Generation
- rating
- StoreName
- Location

Core behavior:

- explicit-vs-inferred field handling via explicitConstraints
- soft vs strict matching (intentMode + strictFilters)
- CPU/GPU tier-aware matching in soft mode
- exact_filter / near_match / no_match modes
- weighted matching and ranking
- candidate deduplication (keep cheapest duplicate)
- detailed rejection log (filter-level failure reasons)

## New: Filter Debug Snapshot

Every filter response now includes filter_debug_snapshot:

```json
{
  "input_fields": {
    "product": "ASUS",
    "price": 150000,
    "category": "laptop",
    "has_explicit_constraints": false,
    "intent_mode": "normal"
  },
  "active_filters_count": 6,
  "candidates_received": 1,
  "rejection_reasons_total": 1,
  "final_mode": "no_match"
}
```

This is intended for observability and fast debugging, not user-facing UI display.

## Filter Contract (Important)

### Input expectations

- input_result should provide:
  - explicitConstraints (dict): source of truth for user-explicit fields
  - intentMode (optional): normal or strict
  - strictFilters (optional): per-field strict enforcement
- search_result should provide:
  - candidates (list): candidate dictionaries with expected product fields

### Output guarantees

filter_agent returns:

- totalFiltered
- filterMode (exact_filter | near_match | no_match)
- message
- filteredResults
- filteredCandidates
- filtersApplied
- filtersSkipped
- rejectedCount
- rejectionLog
- duplicatesRemoved
- filter_debug_snapshot

## Search Agent Behavior (Current)

Search performs strict matching first, then relaxed fallback if needed.

Search result mode:

- true_match
- closest_alternative

Filter layer then applies deterministic post-search filtering and final mode selection.

## Requirements

- Python 3.9+
- Ollama installed and running
- llama3 model available locally
- Packages from requirements.txt:
  - langchain-ollama>=0.2.0
  - langgraph>=0.2.0

Install:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Example prompts:

- I need an ASUS laptop under 150000 with 16GB RAM and RTX 3050
- Suggest a gaming laptop under 200000 with RTX and 16GB RAM

## Tests

Stabilization and regression checks are available:

- python test_fixes.py
- python test_stabilization.py

test_stabilization.py verifies:

- output contract fields
- debug snapshot presence/shape
- behavior across exact_filter, near_match, no_match

## Notes

- Input normalization and enrichment remain in input_agent/input_tools
- Filter logic remains isolated in filter_agent (no input layer edits required)
- Future optional cleanup: move duplicated GPU/CPU matching logic into shared utility
