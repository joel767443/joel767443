import json
import matplotlib.pyplot as plt
from collections import Counter

with open("data/tech_stack.json") as f:
    stack = json.load(f)

counts = Counter(stack)

names = list(counts.keys())
values = list(counts.values())

plt.figure()

plt.bar(names, values)

plt.xticks(rotation=45)

plt.title("Developer Skill Distribution")

plt.tight_layout()

plt.savefig("graphs/skills_chart.png")

print("Skill graph generated.")
