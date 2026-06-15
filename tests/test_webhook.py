import hmac
import hashlib
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Patch config before importing main (so it doesn't raise on missing .env)
with patch.dict("os.environ", {
    "GITHUB_TOKEN": "fake-token",
    "GITHUB_WEBHOOK_SECRET": "test-secret",
    "GROQ_API_KEY": "fake-groq-key"
}):
    from main import app

client = TestClient(app)
SECRET = "test-secret"


def make_signature(payload: bytes, secret: str) -> str:
    """Helper — generate a valid GitHub HMAC signature."""
    return "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()


# ── Health check ────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "PRReviewer is running"


# ── Webhook: bad signature ───────────────────────────────────────────────────

def test_webhook_rejects_invalid_signature():
    payload = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-Hub-Signature-256": "sha256=invalidsignature",
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        }
    )
    assert response.status_code == 401


# ── Webhook: non-PR event is ignored ────────────────────────────────────────

def test_webhook_ignores_non_pr_events():
    payload = json.dumps({"action": "created"}).encode()
    sig = make_signature(payload, SECRET)

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "push",       # not a pull_request event
            "Content-Type": "application/json",
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── Webhook: valid PR event triggers review pipeline ────────────────────────

def test_webhook_triggers_review_on_pr_opened():
    payload = json.dumps({
        "action": "opened",
        "pull_request": {
            "number": 42,
            "diff_url": "https://github.com/fake/diff"
        },
        "repository": {
            "full_name": "fakeuser/fakerepo"
        }
    }).encode()

    sig = make_signature(payload, SECRET)

    with patch("main.review_pr", return_value="Looks good!") as mock_review, \
         patch("main.post_review_comment") as mock_post, \
         patch("requests.get") as mock_get:

        mock_get.return_value = MagicMock(text="diff content here")

        response = client.post(
            "/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json",
            }
        )

    assert response.status_code == 200
    mock_review.assert_called_once_with("diff content here")
    mock_post.assert_called_once_with("fakeuser/fakerepo", 42, "Looks good!")