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

while True:

    url = f"https://api.github.com/user/repos?per_page=100&page={page}"

    response = requests.get(url, headers=headers)

    data = response.json()

    if not data:
        break

    repos.extend(data)

    page += 1

projects = []

for repo in repos:

    project = {
        "name": repo["name"],
        "url": repo["html_url"],
        "language": repo["language"],
        "private": repo["private"]
    }

    projects.append(project)

with open("data/projects.json","w") as f:
    json.dump(projects,f,indent=4)

print(f"Total repos scanned: {len(projects)}")
