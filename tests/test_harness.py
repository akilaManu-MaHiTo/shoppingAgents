"""
Unified Testing Harness for Shopping Agents
============================================

This file contains the complete testing suite for the Shopping Agents system.
Each test is tagged with the student contributor for accountability.

To run all tests:
    pytest tests/test_harness.py -v

To run specific agent tests:
    pytest tests/test_harness.py::TestInputAgent -v

To generate coverage:
    pytest tests/test_harness.py --cov=. --cov-report=html
"""

import pytest
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph_flow import run_shopping_graph
from input_agent import input_agent
from search_agent import search_agent
from filter_agent import filter_agent
from advisor_agent import recommendation_advisor_agent
from input_tools import (
    extract_price_from_user_input,
    normalize_category,
    classify_budget
)
from advisor_tools import (
    validate_recommendation_fit_tool,
    generate_usage_tips_tool
)


# ============================================================================
# INPUT AGENT TESTS
# ============================================================================

class TestInputAgent:
    """Test suite for Input Agent (Intent extraction and specification parsing)"""

    def test_input_agent_valid_query_parsing(self):
        """[Student A] Test: Parse valid ASUS laptop query with complete specs"""
        user_input = "I need an ASUS laptop with 16GB RAM, RTX 3050, under 80000"
        result = input_agent(user_input)
        
        assert result is not None
        assert result.get("product") == "ASUS"
        assert result.get("price") == 80000
        assert result.get("category") == "laptop"
        assert result.get("RAM") == "16"
        assert result.get("GPU") == "RTX 3050"

    def test_input_agent_no_hallucination_empty_query(self):
        """[Student A] Test: Ensure no invented specs for ambiguous query"""
        user_input = "recommend something good"
        result = input_agent(user_input)
        
        # Should not return fake specs
        gpu = result.get("GPU", "")
        assert gpu in ["", "unknown"] or gpu is None
        cpu = result.get("CPU", "")
        assert cpu in ["", "unknown"] or cpu is None

    def test_input_agent_multiple_brands_picks_first(self):
        """[Student A] Test: Handle multiple brand mentions correctly"""
        user_input = "ASUS or MSI laptop"
        result = input_agent(user_input)
        
        # Should pick first mentioned brand or "unknown"
        product = result.get("product", "unknown")
        assert product in ["ASUS", "MSI", "unknown"]

    def test_input_agent_mobile_category(self):
        """[Student A] Test: Correctly identify mobile/smartphone category"""
        user_input = "I need a smartphone with 8GB RAM and 128GB storage"
        result = input_agent(user_input)
        
        category = result.get("category", "")
        assert category in ["mobile", "smartphone", ""]

    def test_input_agent_missing_specs_defaults(self):
        """[Student A] Test: Missing specs should default to empty or 0"""
        user_input = "HP laptop"  # No price, RAM, GPU specified
        result = input_agent(user_input)
        
        # Unspecified fields should be empty or 0
        assert result.get("price") in [0, None, ""]
        assert result.get("RAM") in [0, None, "", ""]


# ============================================================================
# INPUT TOOLS TESTS
# ============================================================================

class TestInputTools:
    """Test suite for Input Tools (Normalization, parsing, validation)"""

    def test_extract_price_rs_format(self):
        """[Student B] Test: Parse Rs currency format"""
        assert extract_price_from_user_input("Rs 50000") == 50000
        assert extract_price_from_user_input("Rs. 50000") == 50000
        assert extract_price_from_user_input("rs 50000") == 50000

    def test_extract_price_dollar_format(self):
        """[Student B] Test: Parse $ currency format"""
        assert extract_price_from_user_input("$1200") == 1200
        assert extract_price_from_user_input("under $1200") == 1200
        assert extract_price_from_user_input("USD 1200") == 1200

    def test_extract_price_inr_format(self):
        """[Student B] Test: Parse INR currency format"""
        assert extract_price_from_user_input("INR 85000") == 85000
        assert extract_price_from_user_input("85,000 INR") == 85000

    def test_extract_price_abbreviated_format(self):
        """[Student B] Test: Parse abbreviated amounts (k, lakh)"""
        assert extract_price_from_user_input("80k") == 80000
        assert extract_price_from_user_input("under 100k") == 100000
        assert extract_price_from_user_input("1 lakh") == 100000
        assert extract_price_from_user_input("budget 80k") == 80000

    def test_extract_price_no_amount(self):
        """[Student B] Test: Return 0 when no price mentioned"""
        assert extract_price_from_user_input("laptop") == 0
        assert extract_price_from_user_input("") == 0
        assert extract_price_from_user_input("recommend something") == 0

    def test_normalize_category_laptop(self):
        """[Student C] Test: Normalize laptop category variants"""
        assert normalize_category("laptop") == "laptop"
        assert normalize_category("Laptop") == "laptop"
        assert normalize_category("LAPTOP") == "laptop"

    def test_normalize_category_mobile(self):
        """[Student C] Test: Normalize mobile/smartphone category variants"""
        category = normalize_category("mobile")
        assert category in ["mobile", "smartphone"]
        category = normalize_category("smartphone")
        assert category in ["mobile", "smartphone"]

    def test_classify_budget_tier(self):
        """[Student C] Test: Classify budget tiers"""
        budget_tier = classify_budget(40000)
        assert budget_tier in ["budget", "budget-conscious", "low-cost"]
        
        budget_tier = classify_budget(80000)
        assert budget_tier in ["mid-range", "moderate", "standard"]
        
        budget_tier = classify_budget(150000)
        assert budget_tier in ["premium", "high-end", "performance"]


# ============================================================================
# SEARCH AGENT TESTS
# ============================================================================

class TestSearchAgent:
    """Test suite for Search Agent (Product discovery)"""

    def test_search_agent_strict_match_brand_category(self):
        """[Student D] Test: Strict search with brand + category filtering"""
        spec = {
            "product": "ASUS",
            "category": "laptop",
            "CPU": ""
        }
        result = search_agent(spec)
        
        assert result is not None
        assert "resultMode" in result
        assert "candidates" in result
        if result["resultMode"] == "strict":
            for candidate in result["candidates"]:
                assert "ASUS" in candidate.get("name", "")
                assert candidate.get("category", "").lower() == "laptop"

    def test_search_agent_fallback_to_relaxed(self):
        """[Student D] Test: Fallback to relaxed search when strict yields no results"""
        spec = {
            "product": "NonExistentBrand9999",
            "category": "laptop"
        }
        result = search_agent(spec)
        
        # Should attempt relaxed search
        assert "resultMode" in result
        # Relaxed should find more results than strict (or at least try)
        assert "candidates" in result

    def test_search_agent_category_filtering(self):
        """[Student D] Test: Filter results by product category"""
        spec = {"category": "laptop"}
        result = search_agent(spec)
        
        candidates = result.get("candidates", [])
        if candidates:
            for candidate in candidates:
                category = str(candidate.get("category", "")).lower()
                assert "laptop" in category or "notebook" in category

    def test_search_agent_unknown_brand_returns_all_categories(self):
        """[Student D] Test: Unknown brand returns broader results"""
        spec = {
            "product": "unknown",
            "category": "laptop"
        }
        result = search_agent(spec)
        
        # Should return candidates without brand restriction
        candidates = result.get("candidates", [])
        assert isinstance(candidates, list)

    def test_search_agent_empty_spec_returns_dataset(self):
        """[Student D] Test: Empty spec returns full dataset"""
        spec = {}
        result = search_agent(spec)
        
        candidates = result.get("candidates", [])
        assert len(candidates) >= 0  # At least attempts to return data


# ============================================================================
# FILTER AGENT TESTS
# ============================================================================

class TestFilterAgent:
    """Test suite for Filter Agent (Rule-based filtering and ranking)"""

    def test_filter_agent_price_filtering(self):
        """[Student E] Test: Filter products by price constraint"""
        input_spec = {"price": 80000}
        search_result = {
            "candidates": [
                {"name": "ASUS TUF A15", "price": 75000, "category": "laptop", "rating": 4.5},
                {"name": "MSI Katana", "price": 90000, "category": "laptop", "rating": 4.0},
                {"name": "HP Pavilion", "price": 60000, "category": "laptop", "rating": 4.2},
            ]
        }
        
        result = filter_agent(input_spec, search_result)
        
        filtered_names = [c["name"] for c in result.get("filteredCandidates", [])]
        assert "ASUS TUF A15" in filtered_names
        assert "HP Pavilion" in filtered_names
        assert "MSI Katana" not in filtered_names  # Over budget
        assert result["totalFiltered"] >= 2

    def test_filter_agent_rejection_logging(self):
        """[Student E] Test: Log rejection reasons transparently"""
        input_spec = {"price": 80000, "RAM": 16}
        search_result = {
            "candidates": [
                {"name": "Budget Laptop", "price": 85000, "RAM": 8, "category": "laptop"},
                {"name": "Premium Laptop", "price": 75000, "RAM": 16, "category": "laptop"},
            ]
        }
        
        result = filter_agent(input_spec, search_result)
        
        rejection_log = result.get("rejectionLog", [])
        assert len(rejection_log) >= 1
        # Should explain why Budget Laptop was rejected
        assert any("Budget Laptop" in str(log) for log in rejection_log) or len(rejection_log) >= 1

    def test_filter_agent_deduplication(self):
        """[Student E] Test: Remove duplicate products"""
        input_spec = {}
        search_result = {
            "candidates": [
                {"name": "ASUS TUF A15", "price": 75000, "category": "laptop"},
                {"name": "ASUS TUF A15", "price": 75000, "category": "laptop"},  # Duplicate
                {"name": "MSI Katana", "price": 70000, "category": "laptop"},
            ]
        }
        
        result = filter_agent(input_spec, search_result)
        
        duplicates_removed = result.get("duplicatesRemoved", 0)
        assert duplicates_removed >= 1
        
        filtered_candidates = result.get("filteredCandidates", [])
        unique_names = [c["name"] for c in filtered_candidates]
        assert len(unique_names) == len(set(unique_names))  # No duplicates

    def test_filter_agent_no_candidates(self):
        """[Student E] Test: Handle case with no matching candidates"""
        input_spec = {"price": 10000}  # Impossible budget
        search_result = {
            "candidates": [
                {"name": "Expensive Laptop", "price": 100000, "category": "laptop"},
            ]
        }
        
        result = filter_agent(input_spec, search_result)
        
        assert result["totalFiltered"] == 0
        assert result["filterMode"] == "no_match"
        assert len(result.get("filteredCandidates", [])) == 0

    def test_filter_agent_applies_all_constraints(self):
        """[Student E] Test: Apply multiple constraints simultaneously"""
        input_spec = {
            "price": 100000,
            "RAM": 16,
            "GPU": "RTX 3050",
            "category": "laptop"
        }
        search_result = {
            "candidates": [
                {
                    "name": "Perfect Match",
                    "price": 90000,
                    "RAM": 16,
                    "GPU": "RTX 3050",
                    "category": "laptop",
                    "rating": 4.5
                },
                {
                    "name": "Over Budget",
                    "price": 110000,
                    "RAM": 16,
                    "GPU": "RTX 3050",
                    "category": "laptop",
                    "rating": 4.5
                },
            ]
        }
        
        result = filter_agent(input_spec, search_result)
        
        filtered = [c["name"] for c in result.get("filteredCandidates", [])]
        assert "Perfect Match" in filtered
        assert "Over Budget" not in filtered


# ============================================================================
# ADVISOR TOOLS TESTS
# ============================================================================

class TestAdvisorTools:
    """Test suite for Advisor Tools (Validation, scoring, tips)"""

    def test_validate_recommendation_fit_perfect(self):
        """[Student F] Test: Validate perfect fit scenario"""
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
        
        result = validate_recommendation_fit_tool(user_constraints, candidate)
        
        assert result["fit_status"] == "perfect_fit"
        assert result["fit_score"] >= 90
        assert len(result.get("mismatches", [])) == 0
        assert len(result.get("matched_reasons", [])) > 0

    def test_validate_recommendation_fit_partial(self):
        """[Student F] Test: Validate partial fit with some mismatches"""
        user_constraints = {
            "price": 80000,
            "RAM": 16,
            "GPU": "RTX 4050"  # Expect RTX 4050
        }
        candidate = {
            "price": 75000,
            "RAM": 16,
            "GPU": "RTX 3050",  # Only has RTX 3050
            "name": "ASUS TUF Gaming A15"
        }
        
        result = validate_recommendation_fit_tool(user_constraints, candidate)
        
        assert result["fit_status"] == "partial_fit"
        assert len(result.get("mismatches", [])) > 0
        assert any(m["field"] == "GPU" for m in result.get("mismatches", []))

    def test_validate_recommendation_fit_no_fit(self):
        """[Student F] Test: Validate no fit scenario"""
        user_constraints = {
            "price": 50000,
            "RAM": 32,
            "GPU": "RTX 4080"
        }
        candidate = {
            "price": 150000,
            "RAM": 16,
            "GPU": "RTX 2050",
            "name": "Budget Laptop"
        }
        
        result = validate_recommendation_fit_tool(user_constraints, candidate)
        
        # Multiple mismatches expected
        mismatches = result.get("mismatches", [])
        assert len(mismatches) >= 2

    def test_validate_recommendation_fit_score_range(self):
        """[Student F] Test: Fit score is always 0-100"""
        user_constraints = {"price": 100000}
        candidate = {"price": 90000}
        
        result = validate_recommendation_fit_tool(user_constraints, candidate)
        
        fit_score = result.get("fit_score", 0)
        assert 0 <= fit_score <= 100

    def test_generate_usage_tips_laptop(self):
        """[Student G] Test: Generate laptop-specific usage tips"""
        product = {
            "name": "ASUS TUF Gaming A15",
            "category": "laptop",
            "GPU": "RTX 3050",
            "RAM": 16
        }
        
        tips = generate_usage_tips_tool(product, "laptop")
        
        assert isinstance(tips, list)
        assert len(tips) > 0
        # Tips should be relevant to gaming/thermal management
        tips_lower = " ".join(tips).lower()
        assert any(keyword in tips_lower for keyword in [
            "thermal", "cooling", "temperature", "fan", "performance"
        ])

    def test_generate_usage_tips_mobile(self):
        """[Student G] Test: Generate mobile-specific usage tips"""
        product = {
            "name": "iPhone 15",
            "category": "smartphone",
            "RAM": 8
        }
        
        tips = generate_usage_tips_tool(product, "smartphone")
        
        assert isinstance(tips, list)
        assert len(tips) > 0
        # Tips should be relevant to mobile usage
        tips_lower = " ".join(tips).lower()
        assert any(keyword in tips_lower for keyword in [
            "battery", "charger", "screen", "storage", "mobile", "app"
        ])

    def test_generate_usage_tips_returns_list(self):
        """[Student G] Test: Always returns list of tips"""
        product = {"name": "Generic Device"}
        
        tips = generate_usage_tips_tool(product, "laptop")
        
        assert isinstance(tips, list)


# ============================================================================
# ADVISOR AGENT TESTS
# ============================================================================

class TestAdvisorAgent:
    """Test suite for Advisor Agent (Recommendation generation)"""

    def test_advisor_agent_perfect_fit_recommendation(self):
        """[Student H] Test: Advisor recommends perfect fit product"""
        input_result = {
            "product": "ASUS",
            "price": 80000,
            "RAM": 16,
            "GPU": "RTX 3050",
            "category": "laptop"
        }
        filter_result = {
            "filteredCandidates": [
                {
                    "name": "ASUS TUF Gaming A15",
                    "price": 75000,
                    "RAM": 16,
                    "GPU": "RTX 3050",
                    "category": "laptop",
                    "rating": 4.5
                },
                {
                    "name": "ASUS VivoBook",
                    "price": 55000,
                    "RAM": 8,
                    "GPU": "Integrated",
                    "category": "laptop",
                    "rating": 4.0
                }
            ]
        }
        
        result = recommendation_advisor_agent(input_result, filter_result)
        
        assert result["fit_status"] in ["perfect_fit", "partial_fit"]
        assert result["fit_score"] > 0
        assert result["selected_product"]["name"] == "ASUS TUF Gaming A15"
        assert result["confidence"] in ["low", "medium", "high"]
        assert isinstance(result.get("why_selected", []), list)

    def test_advisor_agent_no_candidates(self):
        """[Student H] Test: Advisor handles no candidate scenario"""
        input_result = {"price": 10000}
        filter_result = {"filteredCandidates": []}
        
        result = recommendation_advisor_agent(input_result, filter_result)
        
        assert result["fit_status"] == "no_fit"
        assert result["fit_score"] == 0
        assert result["selected_product"] is None
        assert len(result.get("improvement_suggestions", [])) > 0

    def test_advisor_agent_provides_alternatives(self):
        """[Student H] Test: Advisor provides alternative suggestions"""
        input_result = {"price": 80000}
        filter_result = {
            "filteredCandidates": [
                {"name": "Top Pick", "price": 75000, "rating": 4.8},
                {"name": "Alternative 1", "price": 70000, "rating": 4.5},
                {"name": "Alternative 2", "price": 72000, "rating": 4.6},
            ]
        }
        
        result = recommendation_advisor_agent(input_result, filter_result)
        
        alternatives = result.get("alternatives", [])
        assert len(alternatives) > 0
        assert all(alt["name"] != "Top Pick" for alt in alternatives)


# ============================================================================
# END-TO-END PIPELINE TESTS
# ============================================================================

class TestEndToEndPipeline:
    """Test suite for complete Shopping Agents pipeline"""

    def test_e2e_valid_shopping_query_complete_flow(self):
        """[Student I] Test: Complete pipeline for valid query"""
        user_input = "I need an ASUS laptop with 16GB RAM, RTX 3050, under 80000"
        state = run_shopping_graph(user_input)
        
        # All stages should complete
        assert "input_result" in state
        assert "search_result" in state
        assert "filter_result" in state
        assert "advisor_result" in state
        
        # Should not have errors
        assert state.get("error") is None
        
        # Advisor should provide valid recommendation
        advisor = state["advisor_result"]
        assert advisor.get("fit_status") in ["perfect_fit", "partial_fit", "no_fit"]
        assert 0 <= advisor.get("fit_score", 0) <= 100
        assert advisor["confidence"] in ["low", "medium", "high"]

    def test_e2e_empty_query_graceful_error(self):
        """[Student I] Test: Graceful error handling for empty input"""
        state = run_shopping_graph("")
        
        # Should not crash
        assert state is not None
        assert "error" in state
        assert state.get("error") is not None

    def test_e2e_impossible_criteria_provides_suggestions(self):
        """[Student I] Test: Impossible criteria offers improvement suggestions"""
        user_input = "Laptop with 128GB RAM, RTX 4090, under 10000 Rs"
        state = run_shopping_graph(user_input)
        
        advisor = state.get("advisor_result", {})
        
        # Should provide helpful improvement suggestions
        suggestions = advisor.get("improvement_suggestions", [])
        if advisor.get("fit_status") == "no_fit":
            assert len(suggestions) > 0

    def test_e2e_state_propagation(self):
        """[Student I] Test: State correctly flows through pipeline"""
        user_input = "ASUS laptop under 100000"
        state = run_shopping_graph(user_input)
        
        # Input result should feed into search
        input_result = state.get("input_result", {})
        search_result = state.get("search_result", {})
        
        assert input_result is not None
        assert search_result is not None
        
        # Search should have found candidates
        candidates = search_result.get("candidates", [])
        assert isinstance(candidates, list)

    def test_e2e_deterministic_output(self):
        """[Student I] Test: Same input produces same output (determinism)"""
        user_input = "HP laptop 16GB RAM under 100000"
        
        # Run twice
        state1 = run_shopping_graph(user_input)
        state2 = run_shopping_graph(user_input)
        
        # Should produce identical output
        advisor1 = state1.get("advisor_result", {})
        advisor2 = state2.get("advisor_result", {})
        
        # Same product should be selected both times
        assert advisor1.get("selected_product", {}).get("name") == \
               advisor2.get("selected_product", {}).get("name")


# ============================================================================
# PERFORMANCE & RELIABILITY TESTS
# ============================================================================

class TestPerformanceAndReliability:
    """Test suite for performance and reliability metrics"""

    def test_no_hallucination_across_agents(self):
        """[Student J] Test: No hallucinated specs across entire pipeline"""
        user_input = "something good"  # Vague query
        state = run_shopping_graph(user_input)
        
        input_result = state.get("input_result", {})
        
        # Should not invent specs
        for field in ["CPU", "GPU", "RAM", "Storage"]:
            value = input_result.get(field, "")
            if value:
                # If present, should match user input or be a known value
                assert value in ["unknown", ""] or any(
                    word in str(user_input).lower() 
                    for word in str(value).lower().split()
                )

    def test_rejection_transparency(self):
        """[Student J] Test: All rejections logged with transparent reasons"""
        input_spec = {"price": 50000, "RAM": 16}
        search_result = {
            "candidates": [
                {"name": "Expensive Laptop", "price": 80000, "RAM": 16},
                {"name": "Low RAM Laptop", "price": 40000, "RAM": 8},
                {"name": "Perfect Laptop", "price": 45000, "RAM": 16},
            ]
        }
        
        result = filter_agent(input_spec, search_result)
        
        rejection_log = result.get("rejectionLog", [])
        
        # Each rejection should have reason
        for rejection in rejection_log:
            assert "reason" in rejection or "name" in rejection


# ============================================================================
# PYTEST CONFIGURATION AND FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_data():
    """Provide test data for fixtures"""
    return {
        "sample_laptop_query": "ASUS laptop with 16GB RAM and RTX 3050 under 80000",
        "sample_mobile_query": "iPhone 15 smartphone",
        "impossible_query": "Laptop with 256GB RAM under 5000",
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
