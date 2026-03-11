import os
import json
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ------------------------------
# CONFIG
# ------------------------------
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"}
REPOS_JSON = "data/projects.json"
ARCH_JSON = "data/architecture.json"

# Keywords to detect basic architectures
ARCH_KEYWORDS = {
    "API Architecture": ["api"],
    "Microservices": ["micro", "docker-compose", "k8s.yaml"],
    "Machine Learning Systems": ["ai", "ml", ".ipynb", "tensorflow", "torch"],
    "Multi Tenant SaaS": ["saas", "multi-tenant"]
}

# ------------------------------
# STEP 1: Load repos
# ------------------------------
with open(REPOS_JSON) as f:
    projects = json.load(f)

# ------------------------------
# STEP 2: Detect architectures
# ------------------------------
architectures = defaultdict(int)

for p in projects:
    repo_name = p.get("name", "").lower()
    description = (p.get("description") or "").lower()
    topics = [t.lower() for t in p.get("topics", [])]  # GitHub topics if available
    files = [f.lower() for f in p.get("languages", {}).keys()]  # simple proxy for files/languages

    # Combine all text sources
    text_sources = repo_name + " " + description + " " + " ".join(topics) + " " + " ".join(files)

    # Detect architectures
    for arch, keywords in ARCH_KEYWORDS.items():
        if any(k in text_sources for k in keywords):
            architectures[arch] += 1

# ------------------------------
# STEP 3: Save results
# ------------------------------
unique_arch = list(architectures.keys())
with open(ARCH_JSON, "w") as f:
    json.dump(unique_arch, f, indent=4)

# ------------------------------
# STEP 4: Print
# ------------------------------
print("Architecture patterns detected:")
for arch, count in architectures.items():
    print(f"{arch}: {count} repos detected")
