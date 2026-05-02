# Student Contribution Tracking Document

## Overview
This document tracks individual student contributions to the Shopping Agents project. Each student should complete this template for their assigned agent or tool.

---

## Student A: Input Agent & Input Tools

### Agent Developed: Input Agent

**Location**: `input_agent.py`

**Responsibility**: Extract structured product specifications from unstructured natural language user queries using LLM-based intent extraction with rule-based fallback.

**Key Features Implemented**:
- [ ] LLM-based intent extraction using Ollama Llama3
- [ ] Rule-based fallback for robustness when LLM unavailable
- [ ] Multi-currency price parsing (Rs, $, INR, k, lakh)
- [ ] Budget tier classification
- [ ] History integration for multi-turn context awareness
- [ ] Category normalization
- [ ] Brand identification and validation

**Code Statistics**:
- Lines of code: ___
- Functions implemented: ___
- Test cases contributed: ___ (See `tests/test_harness.py::TestInputAgent`)

**Challenges Faced**:

1. **Challenge**: Preventing LLM hallucination (inventing specs not in user input)
   - **Root Cause**: LLM tendency to generate plausible but unverified information
   - **Solution Implemented**: 
     - Strict prompt engineering with explicit "DO NOT guess values" rules
     - Schema validation against known brands and categories
     - Fallback to empty JSON when LLM is uncertain
   - **Verification**: Test `test_input_agent_no_hallucination_empty_query` validates this

2. **Challenge**: Parsing complex price formats (Rs 80,000 vs $1200 vs 80k vs 1 lakh)
   - **Root Cause**: Multiple currency formats and abbreviations in Indian market
   - **Solution Implemented**:
     - Regex-based multi-format currency parser
     - Support for currency symbols (₹, $, INR, Rs)
     - Support for abbreviations (k, lakh, m, mn)
     - Context-aware extraction (budget, price, under, around)
   - **Verification**: Tests in `TestInputTools::test_extract_price_*`

3. **Challenge**: Handling Ollama model unavailability gracefully
   - **Root Cause**: Ollama server might not be running; shouldn't crash system
   - **Solution Implemented**:
     - Try/except wrapper with model not found detection
     - Fallback to rule-based extraction without LLM
     - Informative error logging
   - **Verification**: System continues functioning in offline mode

**GitHub Evidence**:
- Commits: ___
- PR: ___
- Code Review: ___

---

### Tool Implemented: Input Tools Library

**Location**: `input_tools.py`

**Responsibility**: Provide data normalization, enrichment, and validation utilities for input processing.

**Functions Implemented**:
- [ ] `clean_json()` - Safe JSON extraction from LLM response
- [ ] `validate_input()` - Schema compliance validation
- [ ] `normalize_category()` - Category standardization
- [ ] `normalize_product_brand()` - Brand name normalization
- [ ] `extract_price_from_user_input()` - Multi-format currency parsing
- [ ] `enrich_specs()` - Derived field calculation
- [ ] `log_input()` - Operational logging
- [ ] `classify_budget()` - Budget tier mapping

**Test Coverage**:
- Unit tests written: ___
- Code coverage: ___%
- All functions tested: Yes / No

**Key Implementation Details**:

```python
# Example: Currency parsing edge case
extract_price_from_user_input("under Rs 80,000 but budget 100k")
# Returns: 80000 (priority: explicit amount > context amount)
```

**Challenges Faced**:

1. **Challenge**: Handling malformed JSON from LLM
   - **Solution**: Regex-based JSON cleanup (missing quotes, trailing commas)

2. **Challenge**: Differentiating specs from prices (e.g., "16GB" could be RAM or storage)
   - **Solution**: Context-aware extraction using surrounding keywords

---

## Student B: Search Agent

### Agent Developed: Search Agent

**Location**: `search_agent.py`

**Responsibility**: Perform efficient product discovery from CSV dataset using strict and relaxed search strategies.

**Key Features Implemented**:
- [ ] Strict search (brand + category + spec matching)
- [ ] Relaxed search fallback (broader matching)
- [ ] Full-text search on product names
- [ ] Fuzzy matching on specifications
- [ ] CPU tier-aware matching (i3 < i5 < i7)
- [ ] GPU tier-aware matching (RTX 2050 < 3050 < 4050)
- [ ] Storage range handling (e.g., "128GB - 256GB")
- [ ] Result mode reporting (strict/relaxed/closest_alternative)

**Code Statistics**:
- Lines of code: ___
- Search algorithm complexity: O(n) for dataset
- Fallback mechanism implemented: Yes / No

**Challenges Faced**:

1. **Challenge**: Matching user-specified CPU tiers with product CPU names
   - **Root Cause**: Inconsistent CPU naming in dataset (i5-11800H vs Intel i5)
   - **Solution Implemented**:
     - Regex-based CPU tier extraction
     - Tier comparison (numeric: 3, 5, 7, 9)
     - Vendor matching (Intel vs AMD Ryzen)
   - **Verification**: Test `test_search_agent_cpu_tier_matching`

2. **Challenge**: Handling empty or missing specifications
   - **Root Cause**: Dataset incomplete; some products lack GPU/Storage info
   - **Solution Implemented**:
     - Default values (empty string defaults to match any)
     - Optional field matching (only check if user specified)
   - **Verification**: System returns candidates even with partial info

3. **Challenge**: Performance with large dataset
   - **Root Cause**: CSV with hundreds of products
   - **Solution Implemented**:
     - Single-pass filtering
     - Early termination when limits met
   - **Performance**: < 50ms for typical queries

**GitHub Evidence**:
- Commits: ___
- PR: ___

---

## Student C: Filter Agent

### Agent Developed: Filter Agent

**Location**: `filter_agent.py`

**Responsibility**: Apply deterministic rule-based filtering, ranking, and rejection logging to search candidates.

**Key Features Implemented**:
- [ ] Hardware tier matching (CPU, GPU, RAM validation)
- [ ] Price constraint filtering
- [ ] Storage requirement matching
- [ ] Deduplication by product name
- [ ] Rejection logging with transparent reasons
- [ ] Field-weighted ranking system
- [ ] Filter mode reporting (strict/relaxed/no_match)

**Filtering Pipeline**:
1. Hardware tier validation (pass/fail per candidate)
2. Price filtering (reject over-budget)
3. Deduplication (remove exact duplicates)
4. Rejection logging (track all rejections)
5. Ranking (by field weights)

**Field Weights Implemented**:
```
GPU: 30 (most important for gaming)
CPU: 20
Price: 20
RAM: 15
Storage: 15
Generation: 10
Brand: 10
Category: 10
Storage Type: 8
Rating: 6
StoreName: 6
Location: 6
```

**Test Coverage**:
- Test cases written: ___ (See `TestFilterAgent` in test harness)
- Coverage: ___%

**Challenges Faced**:

1. **Challenge**: Transparent rejection logging for user understanding
   - **Root Cause**: Users need to understand why products were filtered out
   - **Solution Implemented**:
     - Rejection log with detailed reasons
     - Field-by-field mismatch reporting
     - Actionable guidance in rejection messages
   - **Example**:
     ```json
     {
       "product": "MSI Katana",
       "reason": "GPU tier below i5 (Integrated vs RTX 3050)"
     }
     ```

2. **Challenge**: Avoiding over-filtering (too strict)
   - **Root Cause**: Initial strict rules rejected too many valid candidates
   - **Solution Implemented**:
     - Threshold-based matching (e.g., ≥ required tier)
     - Graceful degradation (partial matches acceptable)
     - Clear mode reporting (strict vs relaxed vs no_match)

3. **Challenge**: Handling duplicate products with minor price differences
   - **Root Cause**: Same laptop listed with different prices/colors
   - **Solution Implemented**:
     - Deduplication by name first
     - Keeps lowest-price variant
     - Tracks duplicates removed count

**GitHub Evidence**:
- Commits: ___
- PR: ___

---

## Student D: Advisor Agent & Advisor Tools

### Agent Developed: Advisor Agent

**Location**: `advisor_agent.py`

**Responsibility**: Generate final AI-powered recommendations with fit validation, alternatives, and usage tips.

**Key Features Implemented**:
- [ ] Fit validation using custom tools
- [ ] Usage tips generation
- [ ] Alternative suggestion ranking
- [ ] Improvement suggestion generation
- [ ] Confidence scoring (low/medium/high)
- [ ] Why-selected rationale generation
- [ ] LLM-based explanation with fact grounding

**Recommendation Output**:
```json
{
  "fit_status": "perfect_fit|partial_fit|no_fit",
  "fit_score": 0-100,
  "selected_product": {...},
  "why_selected": [list of reasons],
  "mismatches": [list of mismatches],
  "alternatives": [up to 2 alternatives],
  "improvement_suggestions": [actionable tips],
  "usage_tips": [category-specific tips],
  "confidence": "low|medium|high"
}
```

**Guardrails Implemented**:
- [ ] Fact-based only (no hallucination)
- [ ] Confidence calibration (high ≥ 85% fit score)
- [ ] Mismatch-to-suggestion mapping
- [ ] Alternative diversity (different price points)

**Test Coverage**:
- Test cases: ___ (See `TestAdvisorAgent`)
- Coverage: ___%

**Challenges Faced**:

1. **Challenge**: Generating meaningful "why_selected" explanations grounded in facts
   - **Root Cause**: LLM can hallucinate or over-generalize
   - **Solution Implemented**:
     - Use validation tool results as ground truth
     - Only explain based on matched_reasons from validation
     - Fallback to validation data if LLM response questionable
   - **Verification**: Test `test_advisor_agent_perfect_fit_recommendation`

2. **Challenge**: Calibrating confidence scores appropriately
   - **Root Cause**: All recommendations might report high confidence incorrectly
   - **Solution Implemented**:
     - Confidence tied to fit_score (low: <60%, medium: 60-85%, high: >85%)
     - Validate against mismatch count
     - Conservative scoring strategy
   - **Verification**: Confidence levels consistent with fit_score

3. **Challenge**: Generating helpful improvement suggestions from no-fit scenarios
   - **Root Cause**: Users need actionable next steps when no product matches
   - **Solution Implemented**:
     - Map mismatches to specific suggestions
     - Price mismatch → "Increase budget by 5-10%"
     - GPU mismatch → "Relax GPU tier for affordability"
     - No candidates → "Relax brand or budget constraints"

### Tool Implemented: Advisor Tools

**Location**: `advisor_tools.py`

**Functions Implemented**:
- [ ] `validate_recommendation_fit_tool()` - Fit validation and scoring
- [ ] `generate_usage_tips_tool()` - Category-specific tips

**Function 1: validate_recommendation_fit_tool**

**Purpose**: Compare user constraints vs. candidate product to generate fit score and validation details

**Input**:
```python
user_constraints = {
    "price": 80000,
    "RAM": 16,
    "GPU": "RTX 3050",
    "CPU": "i7"
}
candidate = {
    "price": 75000,
    "RAM": 16,
    "GPU": "RTX 3050",
    "CPU": "i7",
    "name": "ASUS TUF Gaming A15"
}
```

**Output**:
```python
{
    "fit_score": 95,
    "fit_status": "perfect_fit",
    "matched_reasons": [
        "Price within budget (75000 <= 80000)",
        "RAM matched (16GB >= 16GB)",
        "GPU matched (RTX 3050)",
        "CPU matched (i7)"
    ],
    "mismatches": [],
    "checks": {"price": True, "RAM": True, "GPU": True, "CPU": True}
}
```

**Function 2: generate_usage_tips_tool**

**Purpose**: Generate category-specific optimization tips based on product specifications

**Input**:
```python
product = {
    "name": "ASUS TUF Gaming A15",
    "category": "laptop",
    "GPU": "RTX 3050",
    "RAM": 16
}
category = "laptop"
```

**Output**:
```python
[
    "Enable Performance Mode in BIOS for sustained FPS gaming",
    "Clean dust vents every 3-6 months for thermal efficiency",
    "Use SSD-aware defragmentation (TRIM) monthly",
    "Install latest GPU drivers from NVIDIA GeForce Experience"
]
```

**Challenges Faced**:

1. **Challenge**: Making fit scoring transparent and reproducible
   - **Solution**: Weight-based scoring with documented field weights

2. **Challenge**: Generating contextually relevant tips
   - **Solution**: Category-specific tip templates with product-specific customization

**GitHub Evidence**:
- Commits: ___
- PR: ___

---

## Student E: Testing & Integration

### Contributions: Testing Harness

**Location**: `tests/test_harness.py`

**Responsibility**: Create unified testing framework covering all agents and tools with per-student test case assignment.

**Test Suites Implemented**:
- [ ] `TestInputAgent` - Input agent unit tests
- [ ] `TestInputTools` - Input tool library tests
- [ ] `TestSearchAgent` - Search agent tests
- [ ] `TestFilterAgent` - Filter agent tests
- [ ] `TestAdvisorTools` - Advisor tool tests
- [ ] `TestAdvisorAgent` - Advisor agent tests
- [ ] `TestEndToEndPipeline` - Complete pipeline tests
- [ ] `TestPerformanceAndReliability` - Performance and reliability tests

**Test Execution**:
```bash
# Run all tests
pytest tests/test_harness.py -v

# Run with coverage
pytest tests/test_harness.py --cov=. --cov-report=html

# Run specific test class
pytest tests/test_harness.py::TestInputAgent -v
```

**Coverage Target**: ≥ 80% code coverage

**Test Case Distribution**:
- Input Agent: 5 tests
- Search Agent: 5 tests
- Filter Agent: 6 tests
- Advisor Tools: 7 tests
- Advisor Agent: 3 tests
- End-to-End: 5 tests
- Performance: 2 tests
- **Total**: 33+ test cases

**Challenges Addressed**:

1. **Challenge**: Mocking external dependencies (Ollama LLM, CSV file)
   - **Solution**: Tests use actual LLM and dataset for integration testing
   - **Fallback**: Can add mock fixtures if needed

2. **Challenge**: Ensuring test isolation
   - **Solution**: Each test uses self-contained data; no shared state

3. **Challenge**: Making tests fail gracefully when Ollama unavailable
   - **Solution**: Tests check for LLM availability; skip if not available

**GitHub Evidence**:
- Commits: ___
- PR: ___

---

## Student F-J: Additional Contributors

### [Student F Name]: [Role/Component]

**Contributions**:
- [ ] 
- [ ] 

**Challenges**:
1. 
2. 

**GitHub Evidence**:
- Commits: ___
- PR: ___

---

## Summary Statistics

### Code Distribution
| Component | Lines | Functions | Tests |
|-----------|-------|-----------|-------|
| input_agent.py | ___ | ___ | 5 |
| input_tools.py | ___ | ___ | 6 |
| search_agent.py | ___ | ___ | 5 |
| filter_agent.py | ___ | ___ | 6 |
| advisor_agent.py | ___ | ___ | 3 |
| advisor_tools.py | ___ | ___ | 7 |
| langgraph_flow.py | ___ | ___ | - |
| app.py | ___ | ___ | - |
| **TOTAL** | ___ | ___ | 32+ |

### Test Coverage
- **Target Coverage**: ≥ 80%
- **Actual Coverage**: ___%
- **All Critical Paths Tested**: Yes / No

### Git Contribution Summary
```bash
# Generate with:
git shortlog -sn --all
```

| Student | Commits | PR | Code Review |
|---------|---------|----|-----------  |
| Student A | ___ | ___ | ___ |
| Student B | ___ | ___ | ___ |
| Student C | ___ | ___ | ___ |
| Student D | ___ | ___ | ___ |
| Student E | ___ | ___ | ___ |

---

## Verification Checklist

- [ ] All agents implemented and tested
- [ ] All custom tools implemented and tested
- [ ] Unified test harness created with 30+ test cases
- [ ] Each student contributed specific test cases
- [ ] GitHub commits properly attributed
- [ ] Pull requests reviewed and merged
- [ ] Code coverage ≥ 80%
- [ ] Technical report completed
- [ ] This contribution document completed

---

## Submission Instructions

1. **Complete this template** for your assigned component
2. **Update GitHub statistics** with actual numbers (use `git log`, `wc -l`)
3. **Link test cases** you implemented in the test harness
4. **Document challenges** in detail with solutions
5. **Provide GitHub evidence** (commit SHAs, PR numbers)
6. **Get sign-off** from team lead and instructor

---

**Document Version**: 1.0
**Date Completed**: ___________
**Team Lead Sign-off**: ___________
**Instructor Verification**: ___________

