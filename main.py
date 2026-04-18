from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
from config import GITHUB_WEBHOOK_SECRET
from reviewer import review_pr
from github_client import post_review_comment

app = FastAPI()

def verify_signature(payload: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.get("/")
def health_check():
    return {"status": "PRReviewer is running"}

@app.post("/webhook")
async def webhook(request: Request):
    # 1. Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    # 2. Verify it's really from GitHub
    if not verify_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 3. Parse the event
    data = await request.json()
    event = request.headers.get("X-GitHub-Event", "")

    # 4. Only handle PR opened/reopened events
    if event == "pull_request" and data.get("action") in ["opened", "reopened"]:
        pr = data["pull_request"]
        repo_name = data["repository"]["full_name"]
        pr_number = pr["number"]
        diff_url = pr["diff_url"]

        print(f" PR #{pr_number} opened in {repo_name}")

        # 5. Fetch the actual diff
        import requests
        diff_response = requests.get(diff_url)
        diff = diff_response.text

        # 6. Generate the review
        review = review_pr(diff)

        # 7. Post it to GitHub
        post_review_comment(repo_name, pr_number, review)

    return {"status": "ok"}