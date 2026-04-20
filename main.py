from langgraph_flow import run_shopping_graph

user_input = input("Enter your request: ")

state = run_shopping_graph(user_input)
input_result = state.get("input_result", {})
search_result = state.get("search_result", {})
error = state.get("error")

if error:
	print("\nWorkflow Error:")
	print(error)

print("\nInput Agent Output:")
print(input_result)

print("\nSearch Agent Output:")
print(search_result)