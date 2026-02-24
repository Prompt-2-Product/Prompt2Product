import os
from typing import List, Dict, Any
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "ui_templates" / "bootstrap"

class UIAssembler:
    @staticmethod
    def load_template(template_name: str) -> str:
        path = TEMPLATES_DIR / f"{template_name}.html"
        if not path.exists():
            return f"<!-- Template {template_name} not found -->"
        return path.read_text(encoding="utf-8")

    @staticmethod
    def render_card(template: str, data: Dict[str, str]) -> str:
        """Simple string replacement for repeatable items like cards."""
        content = template
        for key, value in data.items():
            content = content.replace(f"{{{{ {key} }}}}", str(value))
        return content

    @staticmethod
    def assemble_page(page_plan: Dict[str, Any]) -> str:
        """
        Assembles a complete HTML page from a PagePlan dictionary.
        page_plan schema:
        {
            "filename": "index.html",
            "title": "Page Title",
            "description": "SEO Description",
            "sections": [
                {
                    "type": "hero",
                    "data": { "title": "...", "subtitle": "...", "cta_text": "...", "cta_link": "..." }
                },
                ...
            ]
        }
        """
        base_template = UIAssembler.load_template("base")
        
        # 1. Build Content Body
        body_content = ""
        
        # Inject Navbar (Always first)
        # Using a default navbar or constructing it from page plan?
        # For now, let's assume we want a standard navbar.
        # We need navigation links. In a real app, these might come from a global config.
        # For this implementation, we'll hardcode or deduce standard links.
        navbar_template = UIAssembler.load_template("navbar")
        nav_links_html = ""
        # Standard links
        links = [("Home", "/"), ("About", "/about"), ("Services", "/services"), ("Contact", "/contact")]
        for label, href in links:
            nav_links_html += f'<li class="nav-item"><a class="nav-link" href="{href}">{label}</a></li>'
            
        navbar_html = navbar_template.replace("{{ brand_name }}", page_plan.get("brand_name", "Brand"))
        navbar_html = navbar_html.replace("{{ nav_links }}", nav_links_html)
        
        body_content += navbar_html

        # 2. Build Sections
        for section in page_plan.get("sections", []):
            sec_type = section.get("type", "").lower()
            sec_data = section.get("data", {})
            template = UIAssembler.load_template(sec_type)
            
            # Handle special repeatable content (feature_cards, pricing_cards, etc.)
            if sec_type == "features" and "features" in sec_data:
                # Construct feature cards
                cards_html = ""
                for feature in sec_data["features"]:
                    # Bootstrap card snippet
                    card = f'''
                    <div class="col-lg-4 mb-5 mb-lg-0">
                        <div class="feature bg-primary bg-gradient text-white rounded-3 mb-3"><i class="bi bi-{feature.get("icon", "collection")}"></i></div>
                        <h2 class="h4 fw-bolder">{feature.get("title", "Feature")}</h2>
                        <p>{feature.get("text", "Description")}</p>
                    </div>
                    '''
                    cards_html += card
                template = template.replace("{{ feature_cards }}", cards_html)

            elif sec_type == "pricing" and "plans" in sec_data:
                cards_html = ""
                for plan in sec_data["plans"]:
                    card = f'''
                    <div class="col-lg-4 mb-5">
                        <div class="card h-100 shadow border-0">
                            <div class="card-body p-5">
                                <div class="small text-uppercase fw-bold text-muted">{plan.get("name", "Plan")}</div>
                                <div class="mb-3"><span class="display-4 fw-bold">{plan.get("price", "$0")}</span><span class="text-muted">/mo</span></div>
                                <ul class="list-unstyled mb-4">
                                    {''.join([f'<li class="mb-2"><i class="bi bi-check text-primary"></i> {feat}</li>' for feat in plan.get("features", [])])}
                                </ul>
                                <div class="d-grid"><a class="btn btn-primary" href="#!">{plan.get("cta", "Choose Plan")}</a></div>
                            </div>
                        </div>
                    </div>
                    '''
                    cards_html += card
                template = template.replace("{{ pricing_cards }}", cards_html)
            
            elif sec_type == "testimonials" and "testimonials" in sec_data:
                cards_html = ""
                for t in sec_data["testimonials"]:
                    card = f'''
                    <div class="col-lg-4 mb-5">
                        <div class="card h-100 shadow border-0">
                            <div class="card-body p-4">
                                <p class="card-text fs-5 mb-4">"{t.get("quote", "Great service!")}"</p>
                                <div class="d-flex align-items-center">
                                    <div class="ms-3">
                                        <div class="fw-bold">{t.get("author", "Client")}</div>
                                        <div class="text-secondary">{t.get("role", "Customer")}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    '''
                    cards_html += card
                template = template.replace("{{ testimonial_cards }}", cards_html)

            elif sec_type == "faq" and "questions" in sec_data:
                items_html = ""
                for i, q in enumerate(sec_data["questions"]):
                    item = f'''
                    <div class="accordion-item">
                        <h3 class="accordion-header" id="heading{i}">
                            <button class="accordion-button {'collapsed' if i > 0 else ''}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{i}" aria-expanded="{'true' if i==0 else 'false'}" aria-controls="collapse{i}">
                                {q.get("question", "Question?")}
                            </button>
                        </h3>
                        <div id="collapse{i}" class="accordion-collapse collapse {'show' if i==0 else ''}" aria-labelledby="heading{i}" data-bs-parent="#accordionFAQ">
                            <div class="accordion-body">
                                {q.get("answer", "Answer.")}
                            </div>
                        </div>
                    </div>
                    '''
                    items_html += item
                template = template.replace("{{ faq_items }}", items_html)

            # Generic replacement for top-level data
            for key, value in sec_data.items():
                if isinstance(value, str):
                    template = template.replace(f"{{{{ {key} }}}}", value)
            
            body_content += template

        # Inject Footer
        footer_template = UIAssembler.load_template("footer")
        footer_template = footer_template.replace("{{ brand_name }}", page_plan.get("brand_name", "Brand"))
        footer_template = footer_template.replace("{{ year }}", "2024")
        footer_template = footer_template.replace("{{ footer_text }}", "Empowering your business.")
        body_content += footer_template

        # Final Assembly
        final_html = base_template.replace("{{ content }}", body_content)
        final_html = final_html.replace("{{ title }}", page_plan.get("title", "Page"))
        final_html = final_html.replace("{{ description }}", page_plan.get("description", ""))
        final_html = final_html.replace("{{ custom_css }}", "") # Placeholder for future custom CSS

        return final_html
