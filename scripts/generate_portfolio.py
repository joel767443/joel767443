import json
import os

with open("data/projects.json") as f:
    projects = json.load(f)

html = """
<html>
<head>
<title>Developer Portfolio</title>
</head>

<body>

<h1>Yoweli Kachala</h1>

<h2>Projects</h2>

<ul>
"""

for p in projects:

    html += f'<li><a href="{p["url"]}">{p["name"]}</a> - {p.get("summary","")}</li>'

html += "</ul></body></html>"

os.makedirs("portfolio", exist_ok=True)

with open("portfolio/index.html", "w") as f:
    f.write(html)

print("Portfolio generated.")
