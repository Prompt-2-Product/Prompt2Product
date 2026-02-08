from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel
from app.services.llm.base import LLMClient
from app.services.prompt_to_spec import TaskSpec
import re

class Placeholder(BaseModel):
    """Represents a content placeholder in HTML."""
    id: str
    type: str  # 'comment', 'text', 'attribute'
    context: str  # Surrounding HTML for context
    metadata: Dict[str, Any] = {}

SYSTEM_CONTENT_ENRICH = """You are a world-class copywriter and UX content specialist.

Your task is to replace placeholder content in HTML with RICH, CONTEXTUAL, PROFESSIONAL content.

RULES:
1. **NO Generic Content**: Never use "Lorem ipsum", "Feature 1/2/3", "Click here"
2. **Industry-Specific**: Match the app's purpose and industry
3. **Benefit-Driven**: Focus on user benefits, not features
4. **Action-Oriented CTAs**: Use compelling calls-to-action
5. **Realistic Data**: Testimonials, stats, and examples must be believable
6. **Maintain Structure**: Keep all HTML tags, classes, and IDs exactly as-is

CONTENT GUIDELINES:
- **Hero Titles**: 5-8 words, benefit-focused, emotional hook
- **Descriptions**: 15-25 words, clear value proposition
- **Feature Titles**: 2-4 words, specific and descriptive
- **Feature Descriptions**: 10-15 words, explain the "what" and "why"
- **CTAs**: 2-4 words, action verbs ("Start Free Trial", "Get Instant Access")
- **Testimonials**: 20-30 words, specific results, realistic names/titles
- **Stats**: Industry-appropriate, believable numbers

EXAMPLE TRANSFORMATION:
Input:
```html
<h1><!-- PLACEHOLDER: hero_title --></h1>
<p>Lorem ipsum dolor sit amet</p>
<div class="feature">
  <h3>Feature 1</h3>
  <p>Description here</p>
</div>
```

Output:
```html
<h1>Transform Your Workflow with AI-Powered Automation</h1>
<p>Save 10+ hours per week by automating repetitive tasks with intelligent workflows</p>
<div class="feature">
  <h3>Smart Task Prioritization</h3>
  <p>AI analyzes your workload and suggests optimal task ordering for maximum productivity</p>
</div>
```

OUTPUT FORMAT:
Return ONLY the enriched HTML. No explanations, no markdown blocks.
"""

def extract_placeholders(html: str, page_name: str = "") -> List[Placeholder]:
    """
    Extract placeholders from HTML:
    1. HTML comments: <!-- PLACEHOLDER: ... -->
    2. Generic text: "Lorem ipsum", "Feature 1", etc.
    3. Placeholder images: via.placeholder.com
    """
    placeholders = []
    
    # 1. Find HTML comment placeholders
    comment_pattern = r'<!--\s*PLACEHOLDER:\s*([^-]+?)\s*(?:\|\s*(.+?))?\s*-->'
    for match in re.finditer(comment_pattern, html):
        placeholder_id = match.group(1).strip()
        metadata_str = match.group(2)
        metadata = {}
        if metadata_str:
            # Parse metadata like "max_words: 5, type: title"
            for item in metadata_str.split(','):
                if ':' in item:
                    key, value = item.split(':', 1)
                    metadata[key.strip()] = value.strip()
        
        # Get surrounding context (50 chars before and after)
        start = max(0, match.start() - 50)
        end = min(len(html), match.end() + 50)
        context = html[start:end]
        
        placeholders.append(Placeholder(
            id=placeholder_id,
            type='comment',
            context=context,
            metadata=metadata
        ))
    
    # 2. Find generic text patterns
    generic_patterns = [
        r'\bLorem ipsum\b',
        r'\bFeature \d+\b',
        r'\bDescription here\b',
        r'\bClick here\b',
        r'\bLearn more\b',
    ]
    
    for pattern in generic_patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            placeholders.append(Placeholder(
                id=f"generic_{match.group()}",
                type='text',
                context=html[max(0, match.start()-50):min(len(html), match.end()+50)],
                metadata={'original': match.group()}
            ))
    
    return placeholders

async def enrich_html_content(
    llm: LLMClient,
    model: str,
    html_content: str,
    spec: TaskSpec,
    page_name: str
) -> str:
    """
    Takes skeleton HTML and fills it with rich, contextual content.
    
    Args:
        llm: LLM client
        model: Model name to use
        html_content: Original HTML with placeholders
        spec: TaskSpec for context about the app
        page_name: Name of the page being enriched
    
    Returns:
        Enriched HTML with all placeholders replaced
    """
    # Extract placeholders
    placeholders = extract_placeholders(html_content, page_name)
    
    if not placeholders:
        # No placeholders found, try generic enrichment
        return await generic_content_enrichment(llm, model, html_content, spec, page_name)
    
    # Build context for the LLM
    context = f"""
APP CONTEXT:
- Name: {spec.app_name}
- Industry: {spec.notes or 'General SaaS'}
- Page: {page_name}
- Theme: {spec.styling.theme}

PLACEHOLDERS FOUND: {len(placeholders)}
"""
    
    user_prompt = f"""{context}

ORIGINAL HTML:
{html_content}

TASK: Replace ALL placeholder content with rich, professional content that matches the app's purpose and industry.
Return ONLY the enriched HTML."""
    
    # Call LLM
    enriched = await llm.chat(
        model=model,
        system=SYSTEM_CONTENT_ENRICH,
        user=user_prompt,
        max_tokens=8192
    )
    
    # Clean up any markdown code blocks
    enriched = re.sub(r'```html\s*', '', enriched)
    enriched = re.sub(r'```\s*$', '', enriched)
    
    return enriched.strip()

async def generic_content_enrichment(
    llm: LLMClient,
    model: str,
    html_content: str,
    spec: TaskSpec,
    page_name: str
) -> str:
    """
    Fallback: Enrich HTML even without explicit placeholders.
    Replaces generic content like "Lorem ipsum" and "Feature 1".
    """
    context = f"""
APP: {spec.app_name}
PAGE: {page_name}
PURPOSE: {spec.notes or 'Professional web application'}
"""
    
    user_prompt = f"""{context}

HTML:
{html_content}

TASK: Replace any generic placeholder content (Lorem ipsum, Feature 1/2/3, etc.) with professional, contextual content.
Return ONLY the enriched HTML."""
    
    enriched = await llm.chat(
        model=model,
        system=SYSTEM_CONTENT_ENRICH,
        user=user_prompt,
        max_tokens=8192
    )
    
    # Clean markdown
    enriched = re.sub(r'```html\s*', '', enriched)
    enriched = re.sub(r'```\s*$', '', enriched)
    
    return enriched.strip()
