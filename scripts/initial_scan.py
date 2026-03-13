import base64
import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {TOKEN}"
}


def get_readme_summary(owner: str, repo_name: str) -> str:
    if not TOKEN:
        # If we don't have a token, still try unauthenticated (may fail on private repos).
        readme_headers = {}
    else:
        readme_headers = headers

    url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"
    try:
        response = requests.get(url, headers=readme_headers)
    except requests.RequestException:
        return "No README summary available."

    if response.status_code != 200:
        return "No README summary available."

    try:
        content = base64.b64decode(response.json().get("content", "")).decode()
    except Exception:
        return "No README summary available."

    summary_lines = content.split("\n")[0:5]
    return " ".join(summary_lines) if summary_lines else "No README summary available."


repos = []
page = 1

# Step 1: Get all repos
while True:
    url = f"https://api.github.com/user/repos?per_page=100&page={page}"
    response = requests.get(url, headers=headers)
    data = response.json()
    if not data:
        break
    repos.extend(data)
    page += 1

projects = []
global_language_bytes = {}  # Accumulate bytes for all repos

for repo in repos:
    lang_url = repo["languages_url"]
    lang_response = requests.get(lang_url, headers=headers)
    lang_data = lang_response.json()  # dict: {language: bytes}

    total_bytes = sum(lang_data.values())
    language_percentages = {}

    for lang, bytes_count in lang_data.items():
        if total_bytes > 0:
            pct = round((bytes_count / total_bytes) * 100, 2)
            if pct > 0:  # Only include non-zero percentages
                language_percentages[lang] = pct
                global_language_bytes[lang] = global_language_bytes.get(lang, 0) + bytes_count

    owner = repo["owner"]["login"]
    repo_name = repo["name"]
    summary = get_readme_summary(owner, repo_name)

    project = {
        "name": repo_name,
        "url": repo["html_url"],
        "languages": language_percentages,  # Only non-zero percentages
        "description": repo["description"],
        "private": repo["private"],
        "summary": summary,
    }

    projects.append(project)

# Save per-repo projects with language percentages and README summaries
os.makedirs("data", exist_ok=True)
with open("data/projects.json", "w") as f:
    json.dump(projects, f, indent=4)

# Step 2: Calculate global percentages
total_global_bytes = sum(global_language_bytes.values())
global_percentages = {
    lang: round((bytes_count / total_global_bytes) * 100, 2)
    for lang, bytes_count in global_language_bytes.items()
    if bytes_count > 0  # Filter out 0-byte languages
}

# Print sorted global percentages (most used first)
sorted_global = dict(sorted(global_percentages.items(), key=lambda x: x[1], reverse=True))
print("Global tech stack percentages (most used first):")
for lang, pct in sorted_global.items():
    print(f"{lang}: {pct}%")

print(f"\nTotal repos scanned: {len(projects)}")
