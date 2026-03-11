import json

with open("data/projects.json") as f:
    projects = json.load(f)

tech_stack = []

for p in projects:
    # 'language' is now a list
    languages = p.get("language", [])
    if languages:  # make sure the list is not empty
        tech_stack.extend(languages)

# Remove duplicates and sort
unique_stack = sorted(set(tech_stack))

with open("data/tech_stack.json", "w") as f:
    json.dump(unique_stack, f, indent=4)

print(f"Tech stack extracted. {len(unique_stack)} unique languages found.")
