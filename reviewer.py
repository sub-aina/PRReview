from groq import Groq
from indexer import search_codebase
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def build_prompt(diff: str, context_chunks: list[dict]) -> str:
    context_text = ""
    for chunk in context_chunks:
        context_text += f"\n--- From {chunk['filepath']} ---\n"
        context_text += chunk['content']
        context_text += "\n"

    return f"""You are a senior software engineer doing a code review.

Focus on:
- Bugs or logical errors
- Security vulnerabilities (SQL injection, XSS, hardcoded secrets)
- Inconsistencies with existing codebase patterns
- Missing error handling
- Performance issues

Be specific. Max 5 most important points.

--- EXISTING CODEBASE CONTEXT ---
{context_text}

--- PULL REQUEST DIFF ---
{diff}

--- YOUR REVIEW ---"""

def review_pr(diff: str) -> str:
    print(" Searching codebase for relevant context...")
    context_chunks = search_codebase(diff, n_results=5)

    print(" Sending to Groq for review...")
    prompt = build_prompt(diff, context_chunks)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )

    review = response.choices[0].message.content
    print(" Review generated!")
    return review