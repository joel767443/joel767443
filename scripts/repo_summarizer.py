import requests
import base64
import json

USERNAME = "joel767443"

with open("data/projects.json") as f:
    projects = json.load(f)

for p in projects:

    repo = p["name"]

    url = f"https://api.github.com/repos/{USERNAME}/{repo}/readme"

    r = requests.get(url)

    if r.status_code == 200:

        content = base64.b64decode(r.json()["content"]).decode()

        summary = content.split("\n")[0:5]

        p["summary"] = " ".join(summary)

    else:

        p["summary"] = "No README summary available."

with open("data/projects.json", "w") as f:
    json.dump(projects, f, indent=4)

print("Project summaries added.")
