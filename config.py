from dotenv import load_dotenv
import os

load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Validate all keys are present on startup
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is missing from .env")
if not GITHUB_WEBHOOK_SECRET:
    raise ValueError("GITHUB_WEBHOOK_SECRET is missing from .env")