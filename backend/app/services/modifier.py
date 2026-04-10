from __future__ import annotations
from app.services.llm.base import LLMClient

SYSTEM_MODIFY = """You are an expert full-stack developer.
The user wants to make changes to their generated application.
Use the paths from the context blocks that look like: --- FILE: generated_app/frontend/some.html ---

CRITICAL: Reply with ONLY one of the two formats below. No markdown fences, no explanations, no preamble, no diff --git.

FORMAT A — Patch (preferred):
*** Begin Patch
*** Update File: generated_app/frontend/contact.html
+++ REPLACE ENTIRE FILE +++
(full file from first line to last, unchanged parts copied from context)
*** End Patch

FORMAT B — JSON (only if you cannot use A):
{"files":[{"path":"generated_app/frontend/contact.html","content":"<!DOCTYPE html>\\n...\\n"}]}
Every element MUST have "path" and "content" (complete file). Escape " as \\" and newlines as \\n inside content.

Guidelines:
- If the user says "contact page" / "about page", edit generated_app/frontend/contact.html or about.html — do not invent homepage.html or maps.html.
- Change only files that need edits; always send the FULL file content for each changed file.
- Keep Bootstrap/design consistent with the existing page. Add backend routes only if you add new API needs.

--- Few-shot 1 (FORMAT A) ---
User request: Add a contact form section with name, email, and message fields on the contact page.
Assistant (copy structure; use real content from CURRENT CODE CONTEXT):
*** Begin Patch
*** Update File: generated_app/frontend/contact.html
+++ REPLACE ENTIRE FILE +++
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Contact</title></head>
<body>
<nav><!-- keep same nav as in context --></nav>
<main class="container py-5">
  <h1>Contact</h1>
  <form method="post" action="/api/contact" class="row g-3">
    <div class="col-md-6"><label class="form-label">Name</label><input class="form-control" name="name" required></div>
    <div class="col-md-6"><label class="form-label">Email</label><input type="email" class="form-control" name="email" required></div>
    <div class="col-12"><label class="form-label">Message</label><textarea class="form-control" name="message" rows="4" required></textarea></div>
    <div class="col-12"><button type="submit" class="btn btn-primary">Send</button></div>
  </form>
</main>
</body>
</html>
*** End Patch

--- Few-shot 2 (FORMAT B) ---
User request: Change the hero title on the landing page.
Assistant:
{"files":[{"path":"generated_app/frontend/index.html","content":"<!DOCTYPE html>\\n<html lang=\\"en\\">\\n<head><title>Home</title></head>\\n<body><h1>Welcome</h1></body>\\n</html>\\n"}]}

--- Few-shot 3 (FORMAT A, multiple files — e.g. fix navbar links) ---
User request: Navigation links should go to the correct pages.
Assistant (repeat for every HTML file that contains the navbar; use href paths your FastAPI app serves, e.g. /contact not /contact.html):
*** Begin Patch
*** Update File: generated_app/frontend/index.html
+++ REPLACE ENTIRE FILE +++
<!DOCTYPE html>
<html lang="en">
<body>
<nav class="navbar"><a class="nav-link" href="/">Home</a><a class="nav-link" href="/about">About</a><a class="nav-link" href="/contact">Contact</a></nav>
</body>
</html>
*** Update File: generated_app/frontend/about.html
+++ REPLACE ENTIRE FILE +++
<!DOCTYPE html>
<html lang="en">
<body>
<nav class="navbar"><a class="nav-link" href="/">Home</a><a class="nav-link" href="/about">About</a><a class="nav-link" href="/contact">Contact</a></nav>
<main><h1>About</h1></main>
</body>
</html>
*** End Patch
"""

async def llm_modify(llm: LLMClient, model: str, user_request: str, context: str) -> str:
    user_prompt = f"USER REQUEST: {user_request}\n\nCURRENT CODE CONTEXT:\n{context}\n\nPlease generate a patch to implement the requested changes."
    return await llm.chat(model=model, system=SYSTEM_MODIFY, user=user_prompt, max_tokens=16384)


SYSTEM_MODIFY_JSON_ONLY = """You output ONLY one valid JSON object. No markdown, no code fences, no text before or after.

Required shape (copy this pattern):
{"files":[{"path":"generated_app/frontend/contact.html","content":"FULL_FILE_ONE_STRING"}]}

Rules:
- Top-level key MUST be "files" (array). Forbidden keys: patched_files, unpatched_files, error, message, success.
- Each item MUST have "path" and "content". "content" is the entire HTML/CSS/JS file, not a diff and not a summary.
- Paths MUST match --- FILE: ... --- lines in the user context (e.g. generated_app/frontend/contact.html).
- Inside "content", escape double quotes as \\" and use \\n for newlines.

Few-shot (valid minimal example — real answers must include the full file from context, edited):
{"files":[{"path":"generated_app/frontend/contact.html","content":"<!DOCTYPE html>\\n<html lang=\\"en\\">\\n<head><meta charset=\\"UTF-8\\"><title>Contact</title></head>\\n<body><h1>Hi</h1><form><input name=\\"email\\"></form></body>\\n</html>\\n"}]}

Few-shot (multiple files — same navbar hrefs on every page you touch):
{"files":[{"path":"generated_app/frontend/index.html","content":"...full file..."},{"path":"generated_app/frontend/about.html","content":"...full file..."}]}
"""


async def llm_modify_json_only(llm: LLMClient, model: str, user_request: str, context: str) -> str:
    user = (
        f"USER REQUEST:\n{user_request}\n\nCURRENT CODE CONTEXT:\n{context}\n\n"
        "Respond with the JSON object only."
    )
    return await llm.chat(model=model, system=SYSTEM_MODIFY_JSON_ONLY, user=user, max_tokens=16384)
