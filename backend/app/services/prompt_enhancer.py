from app.services.llm.base import LLMClient

SYSTEM_PROMPT_ENHANCE = """You are a World-Class Product Designer and Systems Architect.
Your mission is to convert a basic user request into a high-density, industry-standard product plan.
The resulting prompt must push the code generator to build a 'Real-World' application that looks like it was made by a professional studio.

Your output must be the IMPROVED PROMPT ONLY. No talk.

REQUIRED DEPTH FOR IMPROVED PROMPT:
1. **The Product Vision**: High-level core value proposition.
2. **Detailed Architectural Sitemap**: (e.g. Landing Page, Dashboard, Pricing, About, Contact, FAQ, Blog/News).
3. **High-Density Feature Sets**: 
   - Don't just say 'Gallery'. Say 'Filterable Bento-box gallery with modal previews and dynamic sorting'.
   - Don't just say 'Contact Form'. Say 'Multi-step interactive form with client-side validation and success micro-animations'.
4. **Legendary UI/UX Standards**:
   - MUST demand 'Glassmorphic surfaces', 'Animated mesh gradients', 'Sticky blur-effect headers', and 'Smooth scroll-reveal animations'.
   - Use 'Standard Professional UI Color Palettes' (e.g. Zinc/Slate with a vibrant Accent).
5. **Data Structure**: Deep data models (e.g. Products needing reviews count, rating averages, stock status).
6. **Tech Constraints**: "Backend: FastAPI, Frontend: HTML/JS/CSS (Tailwind CDN is MANDATORY for all styling)".

VERTICAL-SPECIFIC DEFAULTS:
- If a Portfolio: Must include a Skill Grid, Project Showcase, and Testimonials.
- If a SaaS: Must include a Pricing Matrix, High-Conversion Hero, and Feature Comparison.
- If an Agency: Must include Process Steps, Team Bios, and Client Logos section.
"""

async def llm_enhance_prompt(llm: LLMClient, model: str, user_prompt: str) -> str:
    """
    Enhances the user's prompt to be more suitable for the spec generator.
    """
    # Use the common .chat() interface (system + user)
    # The temperature is set internally by the client implementation or defaults.
    
    response = await llm.chat(
        model=model, 
        system=SYSTEM_PROMPT_ENHANCE, 
        user=f"User Request: {user_prompt}\n\nImproved Prompt:"
    )
    return response.strip()
