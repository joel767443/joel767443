import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {TOKEN}"
}

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

    project = {
        "name": repo["name"],
        "url": repo["html_url"],
        "languages": language_percentages,  # Only non-zero percentages
        "description": repo["description"],
        "private": repo["private"]
    }

    projects.append(project)

# Save per-repo projects with language percentages
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
