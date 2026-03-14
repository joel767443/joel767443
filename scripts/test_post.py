import os

import requests
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────────
# === REQUIRED SETUP (replace these values) ===

# 1. Your OAuth 2.0 access token with scope: w_member_social
#    (Get it via authorization code flow + refresh as needed)
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
# 2. Your LinkedIn person URN / ID (e.g. from "sub" in /v2/userinfo)
PERSON_ID = os.getenv("PERSON_ID")

# 3. Optional: Use the most recent version (update monthly if needed)
#    Current/recent ones: 202511, 202512, 202601, etc. — check docs if errors occur
API_VERSION = '202602'   # Adjust to latest YYYYMM from https://learn.microsoft.com/en-us/linkedin/marketing/versioning

# ────────────────────────────────────────────────

def post_to_linkedin(text: str = "This is a test post from Python script 🚀"):
    url = "https://api.linkedin.com/rest/posts"

    payload = {
        "author": f"urn:li:person:{PERSON_ID}",
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": API_VERSION
    }

    # Important: do NOT follow redirects automatically → helps debug auth/redirect issues
    response = requests.post(url, headers=headers, json=payload, allow_redirects=False)

    print(f"Status Code: {response.status_code}")

    if response.status_code in (200, 201):
        print("Success! Post created.")
        try:
            print("Post URN / ID:", response.json().get("id"))
            print("Full response:", response.json())
        except:
            print("Response body:", response.text)
    else:
        print("Failed.")
        print("Response headers:", response.headers)
        print("Error body:", response.text)


# ────────────────────────────────────────────────
# Run the post
if __name__ == "__main__":
    post_to_linkedin("Hello from my Python script! Testing LinkedIn API in 2026 🌍")