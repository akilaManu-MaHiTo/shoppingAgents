# Shopping Agents - Multi-Agent AI System

Advanced multi-agent shopping assistant powered by **LangGraph** and **Ollama LLM (Llama3)** that intelligently parses user intent, searches a local product dataset, and applies deterministic filtering with AI-driven recommendations.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Flask
```bash
pip install flask
```

### Step 2: Start Ollama Server (in a separate terminal)
```bash
ollama serve
```

Then pull the model:
```bash
ollama pull llama3
```

### Step 3: Run the Web Application
```bash
python app.py
```

**Open in browser**: `http://localhost:5000`

---

## System Overview

This is a **production-grade 4-agent orchestration system** using **LangGraph** for graph-based workflow management. The system employs:

- **LLM (Ollama Llama3)**: For natural language understanding and intent extraction
- **Rule-Based Filtering**: Deterministic matching with tier-aware hardware comparison
- **Recommendation Advisor**: AI-powered fit assessment and improvement suggestions
- **Stateful Processing**: Input history tracking for context-aware recommendations

---

## Complete Architecture

### Core Components

| File | Purpose | Type |
|------|---------|------|
| `main.py` | CLI entrypoint and result display | Entry Point |
| `langgraph_flow.py` | 4-node LangGraph orchestration engine | Orchestration |
| `input_agent.py` | LLM-based intent extraction from user queries | LLM Agent |
| `search_agent.py` | Full-text and fuzzy search on product dataset | Search Engine |
| `filter_agent.py` | Deterministic rule-based filtering & ranking | Filter Engine |
| `advisor_agent.py` | AI-powered recommendation fit assessment | Advisor Agent |
| `input_tools.py` | Data normalization, enrichment, validation | Tools |
| `advisor_tools.py` | Recommendation validation & tip generation | Tools |
| `input_history.py` | State persistence for multi-turn awareness | Persistence |
| `smart_shopping_dataset.csv` | Product database (laptops, phones, etc.) | Data Source |
| `input_history.json` | Saved user input context | State |
| `agent_log.txt` | Append-only operational log | Logging |
| `app.py` | Flask web server backend | Web Server |
| `templates/index.html` | Chat UI interface | Frontend |
| `static/style.css` | Responsive styling | Stylesheet |
| `static/script.js` | Frontend interactivity | JavaScript |

### 4-Node LangGraph Execution Pipeline

```
START
  ↓
┌─────────────────────────────────────┐
│   1. parse_input_node               │
│   - LLM extraction of user intent   │
│   - Rule-based enrichment           │
│   - Price classification            │
│   Output: input_result              │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│   2. search_products_node           │
│   - Strict search first             │
│   - Fallback to relaxed search      │
│   - Category + brand matching       │
│   Output: search_result (candidates)│
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│   3. filter_products_node           │
│   - Hardware tier matching          │
│   - Price validation                │
│   - Deduplication                   │
│   - Rejection logging               │
│   Output: filter_result             │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│   4. recommendation_advisor_node    │
│   - Fit validation & scoring        │
│   - Alternative suggestions         │
│   - Usage tips generation           │
│   Output: advisor_result            │
└─────────────────────────────────────┘
  ↓
END
```

---

## 💻 Web User Interface

### Features

✅ **Beautiful Chat Interface**
- Modern gradient design with responsive layout
- Real-time message streaming
- Loading animations and visual feedback

✅ **Tab Navigation**
- **💬 Chat Tab**: Interactive chat with AI agents
- **📋 History Tab**: Browse all previous searches

✅ **Chat Functionality**
- Type product queries naturally
- Click example buttons for quick start
- View full analysis in detailed modal
- See AI reasoning for recommendations

✅ **History Management**
- View all search history with details
- Search history by keywords
- Filter by budget type (Low/Mid/High)
- Click history items to search again
- Color-coded budget indicators

✅ **Detailed Analysis Modal**
- Input Agent output (what was understood)
- Search Agent results (candidates found)
- Filter Agent details (filters applied)
- Advisor output (recommendation with reasoning)
- Product cards with specifications
- Alternative suggestions and usage tips

### Access the Web UI

**Default URL**: `http://localhost:5000`

**Browser Support**: Chrome, Firefox, Safari, Edge, Mobile Browsers

**Responsive Design**: Works on desktop, tablet, and mobile devices

### CLI vs Web UI

| Feature | CLI | Web UI |
|---------|-----|--------|
| Easy to use | ✓ | ✓✓ |
| Visual interface | ✗ | ✓ |
| History tracking | ✓ | ✓✓ |
| Search history | ✗ | ✓ |
| Full analysis modal | ✗ | ✓ |
| Real-time responses | ✓ | ✓ |
| Mobile friendly | ✗ | ✓ |
| Beautiful design | ✗ | ✓ |

---

## 1. Input Agent (LLM-Powered Intent Extraction)

### Model Configuration
- **LLM**: Ollama Llama3
- **Prompt Strategy**: STRICT, zero-hallucination extraction
- **Fallback**: Rule-based processing if LLM unavailable

### Extracted Fields

```json
{
  "product": "ASUS|MSI|HP|unknown",
  "category": "laptop|mobile|unknown",
  "price": 0,
  "CPU": "Intel i5|Ryzen 5|...",
  "Generation": "11th|12th|13th gen",
  "RAM": "8GB|16GB|32GB",
  "Storage": "256GB|512GB|1TB",
  "Storage Type": "SSD|HDD",
  "GPU": "RTX 3050|RTX 4050|...",
  "explicitConstraints": {...},
  "intentMode": "normal|strict"
}
```

### Key Features

- **History-Aware**: Maintains recent input history for context (up to 5 previous queries)
- **Budget Classification**: Categorizes price intent (budget/mid-range/premium)
- **Field Enrichment**: Validates all fields against known product attributes
- **Multi-Turn Support**: Remembers user preferences across sessions

### Example Extractions

| User Input | Product | Category | Price | Key Specs |
|------------|---------|----------|-------|-----------|
| "ASUS gaming laptop under 150k" | ASUS | laptop | 150000 | GPU likely RTX, high RAM/SSD |
| "HP mobile budget phone" | HP | mobile | 0 (budget) | Low-mid specs |
| "Need Ryzen 5 with 16GB RAM" | unknown | laptop | 0 | CPU: Ryzen 5, RAM: 16GB |

---

## 2. Search Agent (Dual-Mode Search Engine)

### Search Modes

#### Strict Search
- Requires **exact category match**
- **Brand match** (if specified)
- **Storage type** (if specified)
- Returns high-confidence candidates

#### Relaxed Search (Fallback)
- Loosens hardware constraints
- Accepts nearby price ranges
- Matches component tiers instead of exact specs
- Used when strict search returns 0 results

### Matching Logic

- **Brand Matching**: Case-insensitive substring matching
- **Storage Type Matching**: Handles "SSD or HDD" syntax
- **Hardware Tiers**:
  ```
  Intel: i3 < i5 < i7 < i9
  Ryzen: 3 < 5 < 7 < 9
  GPU: GTX < RTX (higher numbers = higher tier)
  ```
- **Generation Matching**: Minimum generation enforcement (11th+ gen recommended)

### Search Pipeline

1. Parse user specs from `input_result`
2. Query dataset with strict filters
3. If `candidates.length == 0`, retry with relaxed constraints
4. Return top candidates with metadata

---

## 3. Filter Agent (Deterministic Rule-Based Filtering)

### Filtering Dimensions

The filter engine validates candidates across **14 dimensions**:

| Dimension | Type | Behavior |
|-----------|------|----------|
| **category** | Categorical | Must match (strict) |
| **brand** | Categorical | Matches if user explicit; else flexible |
| **price** | Numeric | Hard constraint; ±20% tolerance in soft mode |
| **CPU** | Tier-Based | Exact or tier-based matching |
| **Generation** | Numeric | Minimum generation enforcement |
| **RAM** | Numeric | Minimum or exact match |
| **Storage** | Numeric | Minimum size with range tolerance |
| **Storage Type** | Categorical | SSD preferred; HDD acceptable if explicit |
| **GPU** | Tier-Based | Tier matching with fallback to integrated |
| **Rating** | Numeric | Minimum 3.5-star default filter |
| **StoreName** | Categorical | Supported retailers only |
| **Location** | Categorical | Delivery availability |

### Filter Modes

```python
Mode: "exact_filter"
- All constraints strictly enforced
- Minimum matches required

Mode: "near_match"  
- Tight tolerance (±10% price)
- Tier-aware component matching

Mode: "no_match"
- Candidates rejected or below thresholds
- Returns alternatives with improvement suggestions
```

### Field Weighting System

```python
FIELD_WEIGHTS = {
    "GPU": 30,          # Highest impact on ranking
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
```

**Ranking Formula**: `final_score = Σ(field_weight × normalized_score)`

### Deduplication Strategy

- **Key**: Product name + price
- **Rule**: Keep cheapest duplicate; mark others as removed
- **Benefit**: Prevents duplicate results from different retailers

### Output Structure

```json
{
  "totalFiltered": 5,
  "filterMode": "exact_filter",
  "filteredCandidates": [...],
  "filtersApplied": ["category", "price", "CPU"],
  "filtersSkipped": ["GPU"],
  "rejectedCount": 3,
  "duplicatesRemoved": 1,
  "rejectionLog": [
    {
      "product": "XYZ Laptop",
      "reasons": ["Price exceeds budget by 15k", "CPU tier below i5"]
    }
  ],
  "filter_debug_snapshot": {...}
}
```

---

## 4. Recommendation Advisor Agent (AI Fit Assessment)

### Validation Engine

The advisor validates the **top filtered candidate** against user constraints:

- **Fit Score**: 0-100 (higher = better match)
- **Fit Status**: "perfect_fit" | "strong_fit" | "acceptable" | "no_fit"

### Recommendation Output

```json
{
  "fit_status": "strong_fit",
  "fit_score": 82,
  "selected_product": {
    "name": "ASUS TUF Gaming A16",
    "price": 145000,
    "specs": {...}
  },
  "why_selected": [
    "Exceeds CPU requirement (i7-12th vs i5 requested)",
    "Storage matches exactly (512GB SSD)",
    "Price within 5% of budget"
  ],
  "mismatches": [
    {
      "field": "GPU",
      "required": "RTX 4060",
      "actual": "RTX 4050"
    }
  ],
  "alternatives": [
    {
      "name": "HP Omen 16",
      "price": 155000,
      "reason": "Stronger GPU, similar CPU"
    }
  ],
  "improvement_suggestions": [
    "Increase budget by 10k to unlock RTX 4060 options",
    "Relax GPU tier for more affordable laptops"
  ],
  "usage_tips": [
    "Enable High Performance mode in NVIDIA Control Panel",
    "Use external cooling pad for extended gaming sessions"
  ],
  "confidence": "high"
}
```

### Intelligent Features

- **Mismatch Explanation**: Explains exactly which fields don't match
- **Alternative Generation**: Suggests up to 2 alternatives from filtered list
- **Improvement Roadmap**: Actionable suggestions to find better matches
- **Usage Tips**: Category-specific optimization advice
- **Confidence Scoring**: Indicates reliability of recommendation

---

## Data Types & State Management

### ShoppingState (LangGraph TypedDict)

```python
class ShoppingState(TypedDict, total=False):
    user_input: str                    # Raw user query
    input_result: Dict[str, Any]       # Parsed intent
    search_result: Dict[str, Any]      # Search candidates
    filter_result: Dict[str, Any]      # Filtered + ranked
    advisor_result: Dict[str, Any]     # Recommendation
    error: str                         # Error message (if any)
```

### End-to-End Data Flow

```
User Input
  ↓
input_agent → input_result {
  "product": "ASUS",
  "price": 150000,
  "category": "laptop",
  "CPU": "i5",
  "RAM": "16GB",
  "Storage": "512GB",
  "Storage Type": "SSD",
  "explicitConstraints": {...},
  "intentMode": "normal"
}
  ↓
search_agent → search_result {
  "totalMatches": 8,
  "candidates": [
    {"name": "ASUS TUF A16", "price": 145000, ...},
    {"name": "ASUS ROG Zephyrus", "price": 155000, ...},
    ...
  ]
}
  ↓
filter_agent → filter_result {
  "totalFiltered": 5,
  "filteredCandidates": [
    {"name": "ASUS TUF A16", "price": 145000, "score": 92, ...},
    ...
  ],
  "rejectedCount": 3,
  "duplicatesRemoved": 0
}
  ↓
advisor_agent → advisor_result {
  "fit_status": "strong_fit",
  "fit_score": 85,
  "selected_product": "ASUS TUF A16",
  "why_selected": [...],
  "alternatives": [...],
  "usage_tips": [...]
}
  ↓
CLI Output (All results + summary)
```

---

## Error Handling & Resilience

### Multi-Level Fallbacks

1. **LLM Unavailable**: Falls back to rule-based extraction
2. **No Strict Matches**: Retries with relaxed search
3. **Filter Errors**: Returns safe defaults with detailed error log
4. **Advisor Failure**: Displays raw filter results with explanation

### Error Recovery

```python
# Automatic fallback chain:
LLM Extraction → Rule-Based Enrichment → Empty Specs (graceful degradation)

Strict Search → Relaxed Search → No Candidates (clear user messaging)

Filter Processing → Error Capture → Return with Error Context
```

---

## Setup & Quick Start

### Prerequisites

- Python 3.8+
- Ollama installed and running
- 2GB+ available memory

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama server (separate terminal)
ollama serve

# 3. Pull model (first time only)
ollama pull llama3

# 4. Run the agent
python main.py
```

### Example Session

```
Enter your request: I need an ASUS gaming laptop with RTX 4060, 16GB RAM, 512GB SSD under 150k

Input Agent Output:
{
  "product": "ASUS",
  "category": "laptop",
  "price": 150000,
  "GPU": "RTX 4060",
  "RAM": "16GB",
  "Storage": "512GB",
  "Storage Type": "SSD"
}

Search Agent Output:
{
  "totalMatches": 3,
  "candidates": [
    {"name": "ASUS TUF Gaming A16", "price": 145000, ...},
    ...
  ]
}

Filter Agent Output:
{
  "totalFiltered": 2,
  "filterMode": "exact_filter",
  "filteredCandidates": [
    {"name": "ASUS TUF Gaming A16", "score": 94, ...}
  ]
}

Recommendation:
✓ ASUS TUF Gaming A16 - ₹145,000
  Fit Score: 94/100 [strong_fit]
  Why: Exact specs match + 5k under budget
  Tip: Enable High Performance in NVIDIA Control Panel
```

---

## Key Implementation Highlights

### 1. Tier-Aware Hardware Matching
- Recognizes CPU hierarchy (i3 < i5 < i7 < i9)
- GPU tier valuation system
- Supports cross-vendor comparisons (Intel vs AMD)

### 2. Explicit vs Inferred Constraints
- Distinguishes user-stated vs inferred requirements
- Soft matching for inferred; strict for explicit
- Prevents false rejections

### 3. Weighted Ranking System
- 14-dimension scoring with field weights
- GPU & CPU prioritized (30pts, 20pts)
- Price and RAM balanced (20pts, 15pts)

### 4. Multi-History Awareness
- Stores up to 5 recent queries
- Informs future recommendations
- Enables context-aware extraction

### 5. Production-Grade Observability
- Per-request debug snapshots
- Detailed rejection logging
- Append-only operation log (`agent_log.txt`)

---

## Performance Characteristics

| Component | Latency | Notes |
|-----------|---------|-------|
| Input Extraction | 500-1000ms | LLM call; faster with cache |
| Search | 50-100ms | Full-text search on ~500 products |
| Filter | 30-50ms | Rule-based, O(n) complexity |
| Advisor | 200-400ms | Validation + LLM tips generation |
| **Total E2E** | **~1-2 seconds** | Typical flow |

---

## Filter Contract (Important)

### Input Expectations

- `input_result` must provide:
  - `explicitConstraints` (dict): Source of truth for user-explicit fields
  - `intentMode` (optional): "normal" or "strict"
  - `strictFilters` (optional): Per-field strict enforcement flag
  
- `search_result` must provide:
  - `candidates` (list): Candidate dictionaries with product fields

### Output Guarantees

The filter agent returns:

```python
{
  "totalFiltered": int,                          # Count of filtered candidates
  "filterMode": "exact_filter|near_match|no_match",
  "message": str,                                # Mode-specific message
  "filteredResults": Dict or None,               # Legacy field
  "filteredCandidates": List[Dict],              # Ranked products
  "filtersApplied": List[str],                   # Active filter names
  "filtersSkipped": List[str],                   # Disabled filters
  "rejectedCount": int,                          # Count of rejected candidates
  "rejectionLog": List[Dict],                    # Detailed rejection reasons
  "duplicatesRemoved": int,                      # Duplicate products merged
  "filter_debug_snapshot": {                     # Observability
    "input_fields": {...},
    "active_filters_count": int,
    "candidates_received": int,
    "rejection_reasons_total": int,
    "final_mode": str
  }
}
```

---

## System Capabilities & Limitations

### What It Does Well
- ✅ Extracts structured product specs from natural language (LLM + fallback)
- ✅ Performs intelligent hardware tier matching (CPU/GPU hierarchy)
- ✅ Handles price constraints with soft/strict tolerance modes
- ✅ Deduplicates and ranks results using weighted scoring
- ✅ Provides actionable improvement suggestions when no matches found
- ✅ Maintains multi-turn context via input history
- ✅ Recovers gracefully when LLM is unavailable

### Current Limitations
- Only supports laptops and mobile phones (category-constrained)
- Product database is locally cached (dataset.csv) - no real-time pricing updates
- Advisor recommendations are deterministic (no ML-based ranking)
- Supports 3 brands explicitly (ASUS, MSI, HP) - others marked "unknown"
- GPU/CPU tier detection limited to recognized models

---

## Usage Examples

### Example 1: Specific Hardware Request
```
User: "I need an ASUS laptop with i7 12th gen, 16GB RAM, 512GB SSD, RTX 3050, under 150000"

Input Agent parses:
- product: "ASUS"
- category: "laptop"
- CPU: "i7 12th gen"
- RAM: "16GB"
- Storage: "512GB"
- Storage Type: "SSD"
- GPU: "RTX 3050"
- price: 150000

Search Agent finds 5 candidates

Filter Agent applies exact matching → 2 matches

Advisor recommends: ASUS TUF Gaming A16 (fit_score: 92/100)
```

### Example 2: Budget-Based Search
```
User: "Show me gaming laptops under 100000"

Input Agent extracts:
- category: "laptop"
- price: 100000
- intentMode: "normal" (soft constraints)

Search Agent finds 8 candidates (gaming focus inferred)

Filter Agent relaxes specs → 4 good matches

Advisor picks best value: HP Omen 15 (fit_score: 78/100)
Suggests: "Increase budget 20k for RTX 4060 options"
```

### Example 3: No Matches Scenario
```
User: "HP laptop with RTX 4090 and 64GB RAM under 50000"

Filter Agent finds: 0 matches (unrealistic constraints)

Mode: "no_match"

Advisor provides:
- why_selected: None
- mismatches: [
    {"field": "price", "required": "50000", "actual": "180000+"},
    {"field": "GPU", "required": "RTX 4090", "actual": "RTX 2050 max"}
  ]
- improvement_suggestions: [
    "Increase budget to 150000+ for RTX 4090",
    "Relax to RTX 3060 for 50000-80000 range"
  ]
```

---

## Dependencies & Environment

### Required Packages
```
langchain-ollama>=0.2.0    # Ollama LLM integration
langgraph>=0.2.0           # Graph orchestration engine
```

### LLM Runtime
- **Model**: Ollama Llama3 (locally hosted)
- **Memory**: ~4GB for model + 2GB runtime
- **Inference**: CPU (supports GPU acceleration if available)

### Installation Steps

1. **Install Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install & start Ollama**:
   - Download: https://ollama.ai
   - Start server: `ollama serve` (port 11434)
   - Pull model: `ollama pull llama3`

3. **Run the system**:
   
   **Option A: Web UI (Recommended)**
   ```bash
   python app.py
   # Open http://localhost:5000 in browser
   ```
   
   **Option B: Command Line**
   ```bash
   python main.py
   ```

---

## Operational Monitoring

### Output Artifacts

| File | Purpose | Updated |
|------|---------|---------|
| `agent_log.txt` | Append-only operation log | Every request |
| `input_history.json` | Recent query context | Every request |
| `history.json` | Search/filter results cache | Every request |

### Debug Snapshots

Each filter response includes `filter_debug_snapshot`:

```json
{
  "input_fields": {
    "product": "ASUS",
    "price": 150000,
    "category": "laptop",
    "has_explicit_constraints": true,
    "intent_mode": "normal"
  },
  "active_filters_count": 6,
  "candidates_received": 5,
  "rejection_reasons_total": 3,
  "final_mode": "exact_filter"
}
```

Use this for:
- Debugging filter behavior
- Monitoring filter effectiveness
- Understanding why recommendations differ

---

## Development & Customization

### Key Hooks for Customization

1. **New filter dimensions**: Edit `FIELD_WEIGHTS` in `filter_agent.py`
2. **New brands**: Add to product extraction in `input_agent.py`
3. **New categories**: Update `CATEGORY_MAP` in `search_agent.py`
4. **Ranking formula**: Modify `_final_score()` in `filter_agent.py`
5. **Usage tips**: Extend `generate_usage_tips_tool()` in `advisor_tools.py`

### Testing & Validation

```bash
# Quick integration test
python main.py
# Enter: "ASUS laptop 16GB RAM under 150000"

# Verify outputs:
# 1. input_result has explicitConstraints
# 2. search_result includes candidates list
# 3. filter_result includes filter_debug_snapshot
# 4. advisor_result includes fit_score and why_selected
```

---

## Architecture Patterns

### 1. Multi-Agent Orchestration (LangGraph)
- Graph-based workflow (DAG): linear 4-node pipeline
- State management: TypedDict with error propagation
- Isolation: Each node independently testable

### 2. LLM Fallback Strategy
- Primary: Ollama Llama3 for extraction
- Secondary: Rule-based enrichment (if LLM fails)
- Graceful degradation: Empty specs → relaxed search

### 3. Deterministic Filtering
- No randomness: Same input → same output
- Rule-based: No ML/probabilistic ranking
- Transparent: Full rejection reasoning logged

### 4. Staged Matching
1. Strict → high precision, low recall
2. Relaxed → medium precision, high recall
3. Smart fallback: Automatic retry with loosened constraints

### 5. Weighted Scoring
- Multi-dimensional: 14 fields scored independently
- Prioritized: GPU/CPU weighted 2-3x higher
- Normalized: 0-100 scale per field, aggregated linearly

---

## Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| "Model not found" | Ollama server not running | `ollama serve` in terminal 1 |
| 0 results always | Dataset empty | Verify `smart_shopping_dataset.csv` exists |
| Slow extraction | LLM cold start | First call is slower; subsequent calls faster |
| Wrong category | Input extraction failed | Check `intentMode` and `explicitConstraints` |
| Unexpected filters skipped | Field validation failed | Check field type in `search_result.candidates` |

---

## Future Enhancements

- **Real-time pricing**: Integrate web scraping for live updates
- **ML ranking**: Replace weighted scoring with trained ranker
- **Multi-turn refinement**: Allow user feedback to adjust filters
- **More categories**: Extend support (tablets, cameras, etc.)
- **Negotiation logic**: Suggest best store/cashback options
- **Comparison mode**: Side-by-side product comparisons

---

## Support & Feedback

For issues or improvements:
1. Check `agent_log.txt` for operational context
2. Review `filter_debug_snapshot` for filter behavior
3. Verify `input_result.explicitConstraints` matches intent
4. Test with simpler queries first (e.g., "ASUS laptop under 200000")

---

**Last Updated**: May 2, 2026  
**System Status**: Production Ready  
**LLM Model**: Ollama Llama3  
**Node Count**: 4 (parse → search → filter → advise)
