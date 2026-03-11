import json

with open("data/projects.json") as f:
    projects = json.load(f)

tech_stack = []

for p in projects:

    if p["language"]:
        tech_stack.append(p["language"])

unique_stack = list(set(tech_stack))

with open("data/tech_stack.json", "w") as f:
    json.dump(unique_stack, f, indent=4)

print("Tech stack extracted.")
