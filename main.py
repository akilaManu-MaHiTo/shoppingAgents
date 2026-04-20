from agents.input import input_agent
from agents.search import search_agent

user_input = input("Enter your request: ")

input_result = input_agent(user_input)
search_result = search_agent(input_result)

print("\nInput Agent Output:")
print(input_result)

print("\nSearch Agent Output:")
print(search_result)