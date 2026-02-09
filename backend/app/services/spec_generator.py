from __future__ import annotations
from app.services.prompt_to_spec import TaskSpec
from app.services.llm.base import LLMClient

from app.core.utils import extract_json

SYSTEM_SPEC = """You are a Senior Solution Architect. Convert a detailed technical prompt into a HIGH-DENSITY TaskSpec JSON.
Your goal is to plan a 'Real-World' application that feels deep and feature-rich.

TaskSpec keys:
- app_name (string): A professional name.
- pages: [{name, route, sections:[string]}]
  - YOU MUST PLAN AT LEAST 5 DISTINCT PAGES (e.g. Landing, Features, Pricing, About, Contact).
  - EVERY PAGE MUST HAVE AT LEAST 6 SECTIONS.
  - **CRITICAL**: 'sections' MUST be an array of STRINGS, NOT objects. 
    CORRECT: "sections": ["Hero with gradient", "Bento grid features", "Pricing table"]
    WRONG: "sections": [{"name": "Hero", "desc": "..."}, ...]
  - Section strings should include layout cues: "Bento-style Feature Grid", "Sticky Sidebar with Filters", "Interactive Hero with Mesh Gradient background".
- api: [{method, path, desc}]
  - Plan endpoints for dynamic features (e.g. GET /api/features, POST /api/subscribe).
- data_models: [{name, fields:[{name,type}]}]
- styling: {theme: "light"|"dark", primary_color: hex}
- constraints: {frontend: "html_css", backend: "fastapi"}

GUIDELINES:
1. NEVER plan a basic "MVP". Plan a "Professional Product".
2. Ensure sections describe the 'what' and the 'how' for the UI (animations, layouts).

IMPORTANT:
- Output ONLY valid JSON. No talk. No markdown code blocks.
- Remember: sections is an ARRAY OF STRINGS, not objects!
"""

def repair_spec_json(data: dict) -> dict:
    """
    Repairs common LLM mistakes in spec JSON, like using objects instead of strings for sections.
    """
    if "pages" in data and isinstance(data["pages"], list):
        for page in data["pages"]:
            if "sections" in page and isinstance(page["sections"], list):
                # Convert any object sections to strings
                repaired_sections = []
                for section in page["sections"]:
                    if isinstance(section, dict):
                        # Extract the most relevant field (name or description)
                        section_str = section.get("name", section.get("description", str(section)))
                        repaired_sections.append(section_str)
                    elif isinstance(section, str):
                        repaired_sections.append(section)
                    else:
                        repaired_sections.append(str(section))
                page["sections"] = repaired_sections
    return data

async def llm_prompt_to_spec(llm: LLMClient, model: str, prompt: str) -> TaskSpec:
    user = f"USER_PROMPT:\n{prompt}\n\nReturn TaskSpec JSON only."
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        try:
            raw = await llm.chat(model=model, system=SYSTEM_SPEC, user=user, max_tokens=4096)
            cleaned = extract_json(raw)
            
            # Try to parse as dict first for repair
            import json
            data = json.loads(cleaned)
            data = repair_spec_json(data)
            
            return TaskSpec.model_validate(data)
            
        except Exception as e:
            if attempts >= max_attempts:
                raise e
            
            # Provide specific feedback about the error
            error_msg = str(e)
            fix_system = f"""{SYSTEM_SPEC}

PREVIOUS ERROR: {error_msg}

CRITICAL FIX NEEDED:
- If error mentions 'sections', ensure sections is an ARRAY OF STRINGS: ["string1", "string2"]
- Do NOT use objects in the sections array.

Output ONLY corrected JSON."""
            
            user = f"USER_PROMPT:\n{prompt}\n\nReturn corrected TaskSpec JSON only."
    
    # Fallback (should not reach here)
    raise ValueError("Failed to generate valid TaskSpec after max attempts")
