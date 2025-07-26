import json

# Example: Load and print data from a JSON file named 'data.json'
with open('blog_output.json', 'r') as file:
    data = json.load(file)

print(data.get("content"))