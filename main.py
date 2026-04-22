from langgraph_flow import run_shopping_graph

user_input = input("Enter your request: ")

state = run_shopping_graph(user_input)
input_result = state.get("input_result", {})
search_result = state.get("search_result", {})
filter_result = state.get("filter_result", {})
error = state.get("error")

if error:
	print("\nWorkflow Error:")
	print(error)

print("\nInput Agent Output:")
print(input_result)

print("\nSearch Agent Output:")
print(search_result)

print("\nFilter Agent Output:")
print(filter_result)

if filter_result:
	print("\nFilter Summary:")
	print("Total Filtered:", filter_result.get("totalFiltered", 0))
	print("Filter Mode:", filter_result.get("filterMode", ""))
	print("Applied Filters:", filter_result.get("filtersApplied", []))
	print("Rejected Count:", filter_result.get("rejectedCount", 0))
	print("Duplicates Removed:", filter_result.get("duplicatesRemoved", 0))