import os
import json
import requests
import time
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────────
# CONFIG - CHANGE YOUR GITHUB USERNAME HERE
# ────────────────────────────────────────────────
YOUR_GITHUB_USERNAME = "joel767443"          # ← Change to your actual username (e.g. "joel767443" if that's it)
# If your repos are under an org, change to the org name instead

TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("Warning: No GITHUB_TOKEN → only public repos, low rate limit")

HEADERS = {
    "Authorization": f"token {TOKEN}" if TOKEN else None,
    "Accept": "application/vnd.github+json"
}

REPOS_JSON   = "data/projects.json"
ARCH_JSON    = "data/architecture.json"
CACHE_DIR    = Path("data/cache/files")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Keywords (lowercased)
ARCH_KEYWORDS = {
    "Monolithic Architecture": ["monolith", "monolithic", "single codebase", "all-in-one"],
    "Modular Monolith": ["modular monolith", "modulith", "vertical slice", "feature folder"],
    "Layered Architecture": ["layered", "n-tier", "3-tier", "presentation layer", "business layer", "data access layer"],
    "Hexagonal Architecture": ["hexagonal", "ports and adapters", "clean architecture", "onion architecture"],
    "API Architecture": ["api", "rest api", "graphql", "openapi", "swagger"],
    "Microservices": ["microservice", "microservices", "service mesh", "istio", "linkerd", "docker-compose", "k8s.yaml", "kubernetes", "helm"],
    "Event-Driven Architecture": ["event-driven", "eda", "kafka", "rabbitmq", "pub/sub", "event bus", "event sourcing", "nats", "pulsar"],
    "Serverless Architecture": ["serverless", "lambda", "function as a service", "faas", "aws lambda", "vercel", "netlify functions", "serverless.yml"],
    "CQRS": ["cqrs", "command query", "command-query responsibility segregation", "read model", "write model"],
    "Machine Learning Systems": ["ai", "ml", "machine learning", ".ipynb", "tensorflow", "pytorch", "torch", "scikit-learn", "huggingface", "keras"],
    "Multi Tenant SaaS": ["saas", "multi-tenant", "multi tenancy", "tenant id", "tenant isolation"],
    "Jamstack": ["jamstack", "static site", "static-first", "headless cms", "pre-rendered", "ssg", "next.js static", "gatsby", "hugo"],
    "Micro Frontends": ["micro frontend", "micro-frontends", "module federation", "single-spa"],
    "AI-Native Architecture": ["ai-native", "agentic", "multi-agent", "rag", "retrieval augmented", "ai pipeline"],
    "Edge Computing": ["edge computing", "cloudflare workers", "fastly", "vercel edge", "edge functions", "@edge"]
}

for kws in ARCH_KEYWORDS.values():
    kws[:] = [kw.lower() for kw in kws]

# ────────────────────────────────────────────────
def get_repo_files(owner, repo):
    cache_file = CACHE_DIR / f"{owner}__{repo}.json"
    if cache_file.exists():
        try:
            with cache_file.open() as f:
                return json.load(f)
        except:
            pass

    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 403:
            print(f"Rate limit hit on {owner}/{repo} — sleeping 70s...")
            time.sleep(70)
            resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        if "tree" not in data:
            return []
        files = [item["path"].lower() for item in data["tree"] if item["type"] == "blob"]
        with cache_file.open("w") as f:
            json.dump(files, f)
        return files
    except Exception as e:
        print(f"Failed fetching files for {owner}/{repo}: {e}")
        return []

# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────

with open(REPOS_JSON, encoding="utf-8") as f:
    projects = json.load(f)

print(f"Loaded {len(projects)} repositories\n")

architectures = defaultdict(int)
skipped = 0

for idx, p in enumerate(projects, 1):
    # Robust full_name handling
    full_name = p.get("full_name")
    if not full_name:
        repo_name = p.get("name")
        if not repo_name:
            print(f"[{idx}] Skipping - no name or full_name: {p}")
            skipped += 1
            continue
        owner = YOUR_GITHUB_USERNAME
        full_name = f"{owner}/{repo_name}"
    
    if "/" not in full_name:
        print(f"[{idx}] Skipping malformed repo: {full_name}")
        skipped += 1
        continue

    owner, repo = full_name.split("/", 1)
    repo_lower = repo.lower()

    print(f"[{idx}/{len(projects)}] Processing {full_name} ... ", end="")

    text = " ".join([
        p.get("name", "").lower(),
        (p.get("description") or "").lower(),
        " ".join(t.lower() for t in p.get("topics", [])),
        " ".join(get_repo_files(owner, repo))
    ])

    detected = set()
    for arch, keywords in ARCH_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            detected.add(arch)

    if detected:
        architectures.update({arch: architectures[arch] + 1 for arch in detected})
        print(f"→ {', '.join(detected)}")
    else:
        print("→ no architecture detected")

    time.sleep(1.0)  # Gentle on API

# ────────────────────────────────────────────────
# OUTPUT
# ────────────────────────────────────────────────

if skipped > 0:
    print(f"\nSkipped {skipped} repos due to missing/invalid name/full_name")

unique_arch = sorted(architectures.keys())

output_data = {
    "detected_architectures": unique_arch,
    "counts": dict(architectures),
    "total_repos_processed": len(projects) - skipped,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
}

with open(ARCH_JSON, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print("\n" + "="*70)
print(f"Results saved to {ARCH_JSON}")
print(f"Processed {len(projects) - skipped} / {len(projects)} repos")
if architectures:
    print("Detected architectures:")
    for arch, count in sorted(architectures.items(), key=lambda x: -x[1]):
        print(f"  {arch:28} : {count:3d}")
else:
    print("No architectures detected — check if repos have relevant files (e.g. docker-compose.yml, .ipynb) or increase keyword coverage.")
print("="*70)