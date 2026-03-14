import json
from collections import Counter

import matplotlib.pyplot as plt


def main() -> None:
    with open("data/tech_stack.json") as f:
        stack = json.load(f)

    skill_counts = Counter(stack)
    skill_names = list(skill_counts.keys())
    skill_values = list(skill_counts.values())

    # Load detected architectures data (if available)
    try:
        with open("data/architecture.json") as f:
            arch_data = json.load(f)
        arch_counts = arch_data.get("counts", {})
    except FileNotFoundError:
        arch_counts = {}

    arch_names = list(arch_counts.keys())
    arch_values = list(arch_counts.values())

    # Create combined figure: skills + architectures
    has_arch = bool(arch_counts)

    if has_arch:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=(10, 4))

    # Skills chart
    ax1.bar(skill_names, skill_values)
    ax1.set_title("Developer Skill Distribution")
    ax1.set_xticks(range(len(skill_names)))
    ax1.set_xticklabels(skill_names, rotation=45, ha="right")

    # Architectures chart (if data present)
    if has_arch:
        ax2.bar(arch_names, arch_values, color="tab:orange")
        ax2.set_title("Detected Architectures Across Repositories")
        ax2.set_xticks(range(len(arch_names)))
        ax2.set_xticklabels(arch_names, rotation=45, ha="right")

    fig.tight_layout()
    fig.savefig("graphs/skills_chart.png")

    print("Skill graph (skills + detected architectures) generated.")


if __name__ == "__main__":
    main()
