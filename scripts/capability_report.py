import json
from datetime import datetime

with open("data/projects.json") as f:
    projects = json.load(f)

with open("data/tech_stack.json") as f:
    tech = json.load(f)

num_projects = len(projects)

complexity_score = num_projects * len(tech)

report = f"""
Senior Engineer Capability Report

Generated: {datetime.now()}

Total Projects: {num_projects}

Technologies:
{', '.join(tech)}

Estimated Complexity Score:
{complexity_score}

Architecture Experience:
See architecture.json
"""

with open("reports/capability_report.txt","w") as f:
    f.write(report)

print("Capability report generated.")
