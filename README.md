# PRReviewer
> A bot that auto-reviews every Pull Request the moment it opens — flagging bugs, security holes, and bad patterns. No human trigger needed.

---

## The Flow

```
Developer opens a PR
        ↓
GitHub Webhook → POST to FastAPI server
        ↓
Fetch PR diff (changed lines)
        ↓
ChromaDB → find related codebase files via vector search
        ↓
Groq (Llama 3.3 70B) reads: diff + context → writes review
        ↓
GitHub API posts comments directly on the PR
```

---

## Three Core Problems, Solved

### How does the server know a PR opened?
**GitHub Webhooks** — GitHub sends a POST to your URL on every PR event. You don't poll. GitHub comes to you.

### How does it understand the whole codebase, not just the diff?
**RAG (Retrieval Augmented Generation)** — An indexer pre-reads every file, embeds them into ChromaDB using `all-MiniLM-L6-v2`. When a PR arrives, the diff queries ChromaDB for related files. The LLM sees *context*, not just the change — so it can say *"you're handling auth differently than in `auth.py`"*.

### How do comments appear on the PR?
**PyGithub** — After Groq generates the review, PyGithub posts the comment on the PR.

---

## Tech Stack — All Free

| Tool                          | Role                                         |
| ----------------------------- | -------------------------------------------- |
| **FastAPI**                   | Web server — receives webhooks               |
| **GitHub Webhooks**           | Notifies server on PR open                   |
| **PyGithub**                  | Posts comments to GitHub API                 |
| **Groq**                      | LLM inference — runs Llama 3.3 70B           |
| **ChromaDB**                  | Local vector DB — stores codebase embeddings |
| **SentenceTransformers**      | `all-MiniLM-L6-v2` embedding model           |
| **LangChain Text Splitters**  | Chunks source files before indexing          |
| **Docker**                    | Packages the app into one container          |
| **GitHub Actions**            | CI/CD — tests + build on every push          |
| **pytest**                    | Test suite                                   |
| **ngrok**                     | Exposes local server to GitHub during dev    |

---

## Project Structure

```
PRReviewer/
├── main.py              ← FastAPI app + webhook endpoint
├── indexer.py           ← Reads repo, chunks code, stores in ChromaDB
├── reviewer.py          ← RAG search + Groq LLM call
├── github_client.py     ← Posts comments to GitHub PR
├── config.py            ← Env variable loader
├── tests/
│   ├── test_webhook.py
│   ├── test_indexer.py
│   └── test_reviewer.py
├── .github/
│   └── workflows/
│       └── ci.yml       ← GitHub Actions pipeline (test + docker build)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env                 ← API keys (never committed)
```

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- A [Groq API key](https://console.groq.com)
- A [GitHub personal access token](https://github.com/settings/tokens) with `repo` scope
- ngrok (for local dev)

### 2. Setup

```bash
git clone <repo-url>
cd PRReviewer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

Create `.env` in the project root:

```env
GROQ_API_KEY=gsk_your_key_here
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your_secret_here
```

### 4. Index your codebase

```bash
python -c "from indexer import index_repository; index_repository('.')"
```

### 5. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. Expose via ngrok

```bash
ngrok http 8000
```

### 7. Configure GitHub webhook

In your repo → Settings → Webhooks → Add webhook:

| Field            | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Payload URL      | `https://<your-ngrok>.ngrok.io/webhook`                  |
| Content type     | `application/json`                                       |
| Secret           | Same as `GITHUB_WEBHOOK_SECRET` in `.env`                |
| Events           | Select **Pull requests**                                 |

---

## Running with Docker

```bash
docker compose up --build
```

---

## CI/CD

On every push to `main` or `dev`, GitHub Actions runs:

1. **Run Tests** — installs deps and executes the pytest suite
2. **Build Docker Image** — builds the container (only if tests pass)

---

## Tests

```bash
source venv/bin/activate
pytest tests/ -v
```
