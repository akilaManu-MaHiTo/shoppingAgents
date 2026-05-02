from langgraph_flow import run_shopping_graph
from filter_agent import filter_agent
from advisor_agent import recommendation_advisor_agent

user_input = input("Enter your request: ")

state = run_shopping_graph(user_input)
input_result = state.get("input_result", {})
search_result = state.get("search_result", {})

print("\nInput Agent Output:")
print(input_result)

print("\nSearch Agent Output:")
print(search_result)

# Always ask the follow-up question
print("\nFilter Agent Follow-up Questions:")
print("What is the purpose of buying this laptop? ")
purpose_answer = input("Your answer: ")
filter_result = filter_agent(search_result, input_result, purpose_answer)
advisor_result = recommendation_advisor_agent(input_result, filter_result)

print("\nFilter Agent Output:")
print(filter_result)

print("\nRecommendation Advisor Output:")
print(advisor_result)

if filter_result:
    print("\nFilter Summary:")
    print("Total Filtered:", filter_result.get("totalFiltered", 0))
    print("Filter Mode:", filter_result.get("filterMode", ""))
    print("Applied Filters:", filter_result.get("filtersApplied", []))
    print("Rejected Count:", filter_result.get("rejectedCount", 0))
    print("Duplicates Removed:", filter_result.get("duplicatesRemoved", 0))

if advisor_result:
    print("\nAdvisor Summary:")
    print("Fit Status:", advisor_result.get("fit_status", ""))
    print("Fit Score:", advisor_result.get("fit_score", 0))
    print("Confidence:", advisor_result.get("confidence", ""))