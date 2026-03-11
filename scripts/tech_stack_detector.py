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
TECH_STACK_JSON = "data/tech_stack.json"

# Expanded list of frameworks/tools to detect
FRAMEWORKS = {
    # PHP frameworks
    "Laravel": {"file": "composer.json", "keyword": "laravel/framework"},
    "Symfony": {"file": "composer.json", "keyword": "symfony"},
    "Yii": {"file": "composer.json", "keyword": "yiisoft"},
    "CodeIgniter": {"file": "composer.json", "keyword": "codeigniter"},
    "CakePHP": {"file": "composer.json", "keyword": "cakephp"},
    "Zend": {"file": "composer.json", "keyword": "zendframework"},
    "Phalcon": {"file": "composer.json", "keyword": "phalcon"},
    
    # Python frameworks
    "Django": {"file": "requirements.txt", "keyword": "django"},
    "Flask": {"file": "requirements.txt", "keyword": "flask"},
    "FastAPI": {"file": "requirements.txt", "keyword": "fastapi"},
    "Tornado": {"file": "requirements.txt", "keyword": "tornado"},
    "Pyramid": {"file": "requirements.txt", "keyword": "pyramid"},
    
    # JS/Node frameworks
    "Vue": {"file": "package.json", "keyword": "vue"},
    "React": {"file": "package.json", "keyword": "react"},
    "React Native": {"file": "package.json", "keyword": "react-native"},
    "Angular": {"file": "package.json", "keyword": "angular"},
    "Next.js": {"file": "package.json", "keyword": "next"},
    "Nuxt.js": {"file": "package.json", "keyword": "nuxt"},
    "Express": {"file": "package.json", "keyword": "express"},
    "NestJS": {"file": "package.json", "keyword": "nestjs"},
    
    # Ruby frameworks
    "Rails": {"file": "Gemfile", "keyword": "rails"},
    "Sinatra": {"file": "Gemfile", "keyword": "sinatra"},
    
    # DevOps / Cloud / DB / tools
    "Docker": {"file": "docker-compose.yml", "keyword": None},
    "Kubernetes": {"file": "k8s.yaml", "keyword": None},
    "PostgreSQL": {"file": ".sql", "keyword": None},
    "MySQL": {"file": ".sql", "keyword": None},
    "Redis": {"file": ".conf", "keyword": "redis"},
    "Terraform": {"file": ".tf", "keyword": None},
    "Ansible": {"file": ".yml", "keyword": "ansible"},
}

# ------------------------------
# STEP 1: Load repos
# ------------------------------
with open(REPOS_JSON) as f:
    projects = json.load(f)

# ------------------------------
# STEP 2: Aggregate languages
# ------------------------------
language_totals = defaultdict(float)
for p in projects:
    languages = p.get("languages", {})
    for lang, pct in languages.items():
        if pct > 0:
            language_totals[lang] += pct

# Calculate global percentages
total_sum = sum(language_totals.values())
tech_stack = {lang: round((total / total_sum) * 100, 2) for lang, total in language_totals.items() if total > 0}

# ------------------------------
# STEP 3: Detect frameworks/tools
# ------------------------------
for p in projects:
    repo_name = p["name"]
    repo_url = p["url"]

    # Fetch repo contents from GitHub API
    contents_url = f"https://api.github.com/repos/{repo_url.split('github.com/')[-1]}/contents"
    try:
        resp = requests.get(contents_url, headers=HEADERS)
        if resp.status_code != 200:
            continue
        files = [f["name"] for f in resp.json()]
    except Exception:
        continue

    for fw, fw_data in FRAMEWORKS.items():
        file_name = fw_data["file"]
        keyword = fw_data.get("keyword")
        if any(file_name in f for f in files):
            if keyword is None:
                # Just existence of file is enough
                tech_stack[fw] = tech_stack.get(fw, 0) + 1
            else:
                file_info = next((f for f in resp.json() if f["name"] == file_name), None)
                if file_info and file_info.get("download_url"):
                    file_content = requests.get(file_info["download_url"]).text.lower()
                    if keyword.lower() in file_content:
                        tech_stack[fw] = tech_stack.get(fw, 0) + 1

# ------------------------------
# STEP 4: Sort tech stack by usage/percentage
# ------------------------------
tech_stack_sorted = dict(sorted(tech_stack.items(), key=lambda x: x[1], reverse=True))

# ------------------------------
# STEP 5: Save to JSON
# ------------------------------
with open(TECH_STACK_JSON, "w") as f:
    json.dump(tech_stack_sorted, f, indent=4)

# ------------------------------
# STEP 6: Print results
# ------------------------------
print("Full tech stack with languages and frameworks/tools:")
for tech, pct in tech_stack_sorted.items():
    print(f"{tech}: {pct}")
