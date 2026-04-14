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
    def assemble_page(page_plan: Dict[str, Any], nav_links: List[Dict[str, str]] = None) -> str:
        """
        Assembles a complete HTML page from a PagePlan dictionary.
        nav_links: list of {"label": "Home", "href": "/"}
        """
        base_template = UIAssembler.load_template("base")
        
        # 1. Build Content Body
        body_content = ""
        
        # Inject Navbar (Always first)
        navbar_template = UIAssembler.load_template("navbar")
        nav_links_html = ""
        
        # Use provided links or fallback to Home only
        links = nav_links or [{"label": "Home", "href": "/"}]
        
        for link in links:
            label = link.get("label", "Link")
            href = link.get("href", "#")
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
                    # Premium Feature Card
                    card = f'''
                    <div class="col-lg-4 mb-5">
                        <div class="premium-card p-5 h-100">
                            <div class="feature bg-primary bg-gradient text-white rounded-4 mb-4 d-inline-flex align-items-center justify-content-center" style="width: 60px; height: 60px; font-size: 1.5rem;">
                                <i class="bi bi-{feature.get("icon", "collection")}"></i>
                            </div>
                            <h3 class="h4 mb-3">{feature.get("title", "Feature")}</h3>
                            <p class="text-muted mb-0">{feature.get("text", "Description")}</p>
                        </div>
                    </div>
                    '''
                    cards_html += card
                template = template.replace("{{ feature_cards }}", cards_html)

            elif sec_type == "pricing" and "plans" in sec_data:
                cards_html = ""
                for plan in sec_data["plans"]:
                    card = f'''
                    <div class="col-lg-4 mb-5">
                        <div class="premium-card p-5 h-100 text-center">
                            <div class="small text-uppercase fw-bold text-primary mb-4">{plan.get("name", "Plan")}</div>
                            <div class="mb-4">
                                <span class="display-4 fw-bold gradient-text">{plan.get("price", "$0")}</span>
                                <span class="text-muted">/mo</span>
                            </div>
                            <ul class="list-unstyled mb-5 text-start">
                                {''.join([f'<li class="mb-3 text-muted"><i class="bi bi-check2-circle text-primary me-2"></i> {feat}</li>' for feat in plan.get("features", [])])}
                            </ul>
                            <div class="d-grid">
                                <a class="btn btn-premium" href="#!">{plan.get("cta", "Choose Plan")}</a>
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
                        <div class="premium-card p-5 h-100">
                            <div class="mb-4 text-warning">
                                <i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i>
                            </div>
                            <p class="card-text fs-5 mb-5 text-muted italic">"{t.get("quote", "Great service!")}"</p>
                            <div class="d-flex align-items-center">
                                <div class="flex-shrink-0">
                                    <div class="bg-light rounded-circle d-flex align-items-center justify-content-center" style="width: 50px; height: 50px; background: var(--primary-gradient) !important; color: white;">
                                        {t.get("author", "C")[0]}
                                    </div>
                                </div>
                                <div class="ms-3">
                                    <div class="fw-bold">{t.get("author", "Client")}</div>
                                    <div class="text-muted small">{t.get("role", "Customer")}</div>
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

            elif sec_type == "team" and "members" in sec_data:
                cards_html = ""
                for member in sec_data["members"]:
                    card = f'''
                    <div class="col-lg-4 mb-5">
                        <div class="premium-card p-5 h-100 text-center">
                            <div class="mb-4 d-inline-flex align-items-center justify-content-center rounded-circle" style="width: 100px; height: 100px; background: var(--primary-gradient); color: white; font-size: 3rem;">
                                <i class="bi bi-{member.get("icon", "person-circle")}"></i>
                            </div>
                            <h3 class="h4 mb-2">{member.get("name", "Team Member")}</h3>
                            <div class="small text-uppercase fw-bold text-primary mb-3">{member.get("role", "Expert")}</div>
                            <p class="text-muted mb-0">{member.get("bio", "Dedicated to excellence.")}</p>
                        </div>
                    </div>
                    '''
                    cards_html += card
                template = template.replace("{{ team_cards }}", cards_html)

            # Generic replacement for top-level data
            for key, value in sec_data.items():
                if isinstance(value, str):
                    template = template.replace(f"{{{{ {key} }}}}", value)
            
            body_content += template

        # Ensure we always have AT LEAST a minimal body if LLM failed to provide sections
        if not body_content.strip():
            body_content = '<section class="section-padding text-center"><div class="container"><h1 class="gradient-text">Welcome</h1><p>Building your experience...</p></div></section>'

        # Inject Footer
        footer_template = UIAssembler.load_template("footer")
        footer_template = footer_template.replace("{{ brand_name }}", page_plan.get("brand_name", "Brand"))
        footer_template = footer_template.replace("{{ year }}", "2024")
        
        # Grounded Footer Text
        foot_text = page_plan.get("footer_text") or page_plan.get("description", "Premium digital experiences.")
        footer_template = footer_template.replace("{{ footer_text }}", foot_text)
        body_content += footer_template

        # Final Assembly
        final_html = base_template.replace("{{ content }}", body_content)
        final_html = final_html.replace("{{ title }}", page_plan.get("title", "Page"))
        final_html = final_html.replace("{{ description }}", page_plan.get("description", ""))
        final_html = final_html.replace("{{ custom_css }}", "") # Placeholder for future custom CSS

        return final_html
