from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.llm.base import LLMClient
from app.services.prompt_to_spec import TaskSpec
from app.core.utils import extract_json, repair_json
from app.services.ui_assembler import UIAssembler
import os
import json as json_lib

# --- New Pydantic Models for Page Plan ---
class Section(BaseModel):
    type: str = Field(..., description="Type of section (hero, features, pricing, testimonials, faq, contact, footer)")
    data: Dict[str, Any] = Field(..., description="Data for the section placeholders")

class Page(BaseModel):
    filename: str = Field(..., description="Filename like index.html")
    title: str
    description: str
    sections: List[Section]

class PagePlan(BaseModel):
    brand_name: str
    pages: List[Page]

class GenFile(BaseModel):
    path: str
    content: str
    
class GenOutput(BaseModel):
    files: List[GenFile] = Field(default_factory=list)
    entrypoint: str = "generated_app/backend/main.py"
    run: Dict[str, Any] = Field(default_factory=dict)

# --- Updated System Prompt ---
SYSTEM_CODE = """You are a UI/UX expert planning a website structure.
You do NOT write HTML or Python code. You output a JSON 'Page Plan'.

Your goal is to design a high-converting, professional website using standard Bootstrap 5 components.
Available Section Types: 'hero', 'features', 'pricing', 'testimonials', 'faq', 'contact'.

Refine the user's request into a concrete list of pages and sections.

OUTPUT FORMAT (JSON ONLY):
{
  "brand_name": "LuxeSpaces",
  "pages": [
    {
      "filename": "index.html",
      "title": "Home - LuxeSpaces",
      "description": "Luxury interior design.",
      "sections": [
        {
          "type": "hero",
          "data": {
             "title": "Redefining Luxury Living",
             "subtitle": "Award-winning interior design for modern homes.",
             "cta_text": "View Portfolio",
             "cta_link": "/portfolio.html",
             "secondary_text": "Contact Us",
             "secondary_link": "/contact.html"
          }
        },
        {
          "type": "features",
          "data": {
             "title": "Why Choose Us",
             "subtitle": "Excellence in every detail.",
             "features": [
                {"title": "Custom Design", "text": "Tailored to your lifestyle.", "icon": "palette"},
                {"title": "Expert Team", "text": "Decades of experience.", "icon": "people"}
             ]
          }
        }
      ]
    },
    {
       "filename": "contact.html",
       "title": "Contact Us",
       "description": "Get in touch.",
       "sections": [
          { "type": "contact", "data": { "title": "Get in Touch", "subtitle": "We'd love to hear from you." } }
       ]
    }
  ]
}

RULES:
1. "filename" MUST end in .html (e.g., index.html, about.html).
2. "type" MUST be one of: hero, features, pricing, testimonials, faq, contact.
3. Content should be realistic and professional (no Lorem Ipsum).
4. Create at least 3 pages if the prompt implies a full site (Home, About/Features, Contact).
"""

async def generate_code(llm: LLMClient, model: str, task_spec: TaskSpec) -> GenOutput:
    """
    Generates a Bootstrap-based UI plan and assembles the application code.
    """
    
    # 1. Generate Page Plan using LLM
    # Construct prompt from TaskSpec fields
    description = f"App Name: {task_spec.app_name}"
    if task_spec.notes:
        description += f"\nNotes: {task_spec.notes}"
        
    structure_requirements = "Planned Pages:\n"
    for p in task_spec.pages:
        structure_requirements += f"- {p.name} ({p.route}): {', '.join(p.sections)}\n"

    prompt = f"Design a website for: {description}\n\nStrictly follow this page structure:\n{structure_requirements}"
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        try:
            response = await llm.chat(model=model, system=SYSTEM_CODE, user=prompt)
            
            # Extract and parse JSON
            json_str = extract_json(response)
            if not json_str:
                json_str = response.strip()
                
            try:
                plan_dict = json_lib.loads(json_str)
            except json_lib.JSONDecodeError:
                # Try repair
                json_str_repaired = repair_json(json_str)
                plan_dict = json_lib.loads(json_str_repaired)
                
            page_plan = PagePlan(**plan_dict)
            
            # If successful, break loop
            break
            
        except Exception as e:
            if attempts >= max_attempts:
                print(f"Failed to parse PagePlan after {max_attempts} attempts: {e}")
                raise ValueError(f"LLM failed to generate valid PagePlan: {e}")
            
            # Add error to prompt for next attempt
            print(f"JSON Parse Error (Attempt {attempts}): {e}. Retrying...")
            prompt += f"\n\nERROR: The previous JSON was invalid: {e}\nFix the JSON syntax and return ONLY the JSON."

    # 2. Assemble HTML Files
    gen_files = []
    
    # Frontend Files
    for page in page_plan.pages:
        # Convert Pydantic model to dict for assembler
        page_dict = page.dict()
        page_dict["brand_name"] = page_plan.brand_name
        
        html_content = UIAssembler.assemble_page(page_dict)
        gen_files.append(GenFile(path=f"generated_app/frontend/{page.filename}", content=html_content))

    # 3. Generate Backend (main.py) with dynamic routes
    backend_code = generate_backend_code(page_plan)
    gen_files.append(GenFile(path="generated_app/backend/main.py", content=backend_code))
    
    # 4. Generate Requirements
    reqs = "fastapi\nuvicorn\n"
    gen_files.append(GenFile(path="generated_app/backend/requirements.txt", content=reqs))
    
    return GenOutput(files=gen_files)


def generate_backend_code(plan: PagePlan) -> str:
    """
    Generates FastAPI backend serving the generated HTML pages.
    """
    routes = ""
    for page in plan.pages:
        slug = page.filename.replace(".html", "")
        if slug == "index":
            route_path = "/"
            func_name = "read_root"
        else:
            route_path = f"/{slug}"
            func_name = f"read_{slug.replace('-', '_')}"
            
        routes += f"""
@app.get("{route_path}")
def {func_name}():
    return FileResponse(os.path.join(FRONTEND_DIR, "{page.filename}"))
"""

    return f"""import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Get the parent directory (generated_app/) from backend/
# __file__ is inside backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure directories exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files (if any custom css/js is added later)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ═══════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════
{routes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

# --- Backward Compatibility for Orchestrator ---
llm_spec_to_code = generate_code

def post_process_output(output: GenOutput) -> GenOutput:
    """
    Pass-through for backward compatibility. 
    The new assembler system handles structure, so minimal post-processing needed.
    """
    return output
