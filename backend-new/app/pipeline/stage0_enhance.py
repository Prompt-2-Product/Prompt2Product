import httpx
from app.core.config import OLLAMA_URL, ENHANCE_MODEL

ENHANCE_SYSTEM = """You are a product requirements specialist.
Convert a short vague app idea into ONE detailed sentence describing the application.
Rules:
- Identify key user roles and their core actions
- Mention real features, not vague terms
- Output ONE sentence only. No bullets, no headings, no explanation.
- Keep it under 40 words.
Examples:
Input: fitness app
Output: Build an AI-powered fitness tracking app where users can log workouts, track calories, view progress charts, and join community challenges with leaderboards.
Input: school system
Output: Build a school management system where admins manage students and teachers, teachers post assignments and grades, and students view schedules and results.
Input: ecommerce
Output: Build a multi-vendor ecommerce platform where sellers manage products and inventory, customers browse, add to cart, checkout, and track orders."""

def needs_enhancement(prompt: str) -> bool:
    words = prompt.strip().split()
    word_count = len(words)
    prompt_lower = prompt.lower()

    if word_count <= 4:
        return True

    detail_signals = [
        "page", "pages", "route", "routes",
        "endpoint", "endpoints", "api",
        "table", "database", "db",
        "admin", "seller", "customer", "student", "teacher", "doctor", "patient",
        "login", "register", "signup", "auth",
        "dashboard", "profile", "manage", "track", "list",
        "crud", "upload", "download", "report",
        "cart", "order", "payment", "booking",
        "with", "where", "allows", "can", "should",
    ]

    detail_count = sum(1 for s in detail_signals if s in prompt_lower)

    if word_count >= 5 and detail_count >= 2:
        return False

    if word_count > 15:
        return False

    return True

async def enhance_prompt_async(prompt: str) -> str:
    if not needs_enhancement(prompt):
        return prompt

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": ENHANCE_MODEL,
                    "messages": [
                        {"role": "system", "content": ENHANCE_SYSTEM},
                        {"role": "user", "content": prompt}
                    ],
                    "options": {"temperature": 0.3, "num_predict": 80},
                    "stream": False,
                },
                timeout=60,
            )
            resp.raise_for_status()
            enhanced = resp.json()["message"]["content"].strip()
            
            if len(enhanced.split()) > 60 or len(enhanced) < 10:
                return prompt
                
            return enhanced
    except Exception as e:
        return prompt
