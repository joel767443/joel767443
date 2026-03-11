import json

with open("data/projects.json") as f:
    projects = json.load(f)

architectures = []

for p in projects:

    name = p["name"].lower()

    if "api" in name:
        architectures.append("API Architecture")

    if "micro" in name:
        architectures.append("Microservices")

    if "ai" in name:
        architectures.append("Machine Learning Systems")

    if "saas" in name:
        architectures.append("Multi Tenant SaaS")

unique_arch = list(set(architectures))

with open("data/architecture.json", "w") as f:
    json.dump(unique_arch, f, indent=4)

print("Architecture patterns detected.")
