import json

with open("data/projects.json") as f:
    projects = json.load(f)

with open("data/tech_stack.json") as f:
    tech = json.load(f)

tech_line = " • ".join(tech)

project_lines = ""

for p in projects:

    project_lines += f"- [{p['name']}]({p['url']})\n"

readme = f"""
# Yoweli Kachala

Senior Systems Architect | Full Stack Engineer

## Technologies

{tech_line}

## Projects

{project_lines}

## Skill Graph

![Skills](graphs/skills_chart.png)
"""

with open("README.md","w") as f:
    f.write(readme)

print("Profile README generated.")
