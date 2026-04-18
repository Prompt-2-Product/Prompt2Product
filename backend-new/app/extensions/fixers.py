import re
import os

def fix_template_response(content: str) -> str:
    def replace_old_style(match):
        name = match.group(1)
        context = match.group(2)
        context = re.sub(r"['\"]request['\"]\s*:\s*request\s*,?\s*", "", context).strip()
        context = context.strip("{} \n")
        if context:
            return f"TemplateResponse(request=request, name={name}, context={{{context}}})"
        return f"TemplateResponse(request=request, name={name}, context={{}})"

    content = re.sub(r"TemplateResponse\(\s*(['\"][^'\"]+['\"])\s*,\s*(\{[^}]+\})\s*\)", replace_old_style, content)
    content = re.sub(r"TemplateResponse\(\s*(name\s*=\s*['\"][^'\"]+['\"])", r"TemplateResponse(request=request, \1", content)
    content = re.sub(r"TemplateResponse\(\s*request\s*,\s*(['\"][^'\"]+['\"])\s*,\s*(\{[^}]+\})\s*\)", lambda m: f"TemplateResponse(request=request, name={m.group(1)}, context={m.group(2)})", content)
    
    def replace_dict_return(match):
        context = match.group(1)
        context = re.sub(r"['\"]request['\"]\s*:\s*request\s*,?\s*", "", context).strip()
        context = context.strip("{} \n")
        if context:
            return f"return templates.TemplateResponse(request=request, name='home.html', context={{{context}}})"
        return f"return templates.TemplateResponse(request=request, name='home.html', context={{}})"
    
    content = re.sub(r"return\s+\{\s*['\"]request['\"]\s*:\s*request\s*,?([^}]*)\}", replace_dict_return, content)
    return content

def fix_python_imports(path: str, content: str) -> str:
    fname = os.path.basename(path)

    if fname in ("config.py", "settings.py"):
        return (
            'class Settings:\n'
            '    SECRET_KEY          = "dev_secret_key"\n'
            '    DATABASE_URL        = "sqlite:///./app.db"\n'
            '    DEBUG               = True\n'
            '    APP_NAME            = "App"\n\n'
            'settings = Settings()\n'
        )

    if fname in ("deps.py", "auth.py", "dependencies.py", "security.py"):
        return (
            '# Auth deps stub — jose/passlib replaced\n'
            'from fastapi import HTTPException\n\n'
            'async def get_current_active_user():\n'
            '    return {"id": 1, "name": "Demo User", "email": "demo@example.com"}\n\n'
            'async def get_current_user():\n'
            '    return {"id": 1, "name": "Demo User", "email": "demo@example.com"}\n'
        )

    if fname == "models.py" and ("from tortoise" in content or "from sqlalchemy" in content):
        return (
            '# Auto-generated in-memory db\n'
            'db = {"users": [], "items": [], "records": []}\n\n'
            'class MockModel:\n'
            '    @classmethod\n'
            '    def get_all(cls):\n'
            '        return []\n\n'
            'User = MockModel\n'
        )

    if fname == "session.py" and ("tortoise" in content or "sqlalchemy" in content):
        return '# Session stub\n\ndef get_db():\n    return {}\n'

    content = re.sub(r"from tortoise[^\n]*\n", "", content)
    content = re.sub(r"from sqlalchemy[^\n]*\n", "", content)
    content = re.sub(r"import sqlalchemy[^\n]*\n", "", content)
    content = re.sub(r"from jinja2_fspaths[^\n]*\n", "", content)
    content = re.sub(r"import jinja2_fspaths[^\n]*\n", "", content)
    content = re.sub(r"from jinja2[-_]fs[^\n]*\n", "", content)
    content = re.sub(r"from jose[^\n]*\n", "", content)
    content = re.sub(r"import jose[^\n]*\n", "", content)
    content = re.sub(r"from passlib[^\n]*\n", "", content)
    content = re.sub(r"import passlib[^\n]*\n", "", content)
    content = re.sub(r"from cryptography[^\n]*\n", "", content)
    content = re.sub(r"from app\.core\.config import[^\n]*\n", "", content)
    content = re.sub(r"from app\.config import[^\n]*\n", "", content)
    content = re.sub(r"from config import[^\n]*\n", "", content)
    content = content.replace("from pydantic import BaseSettings", "# BaseSettings removed")
    content = content.replace("from pydantic_settings import BaseSettings", "# BaseSettings removed")

    content = re.sub(r"response_class\s*=\s*templates\.TemplateResponse", "response_class=HTMLResponse", content)

    if fname == "main.py" and "settings." in content and "class Settings" not in content:
        content = re.sub(r"settings\.[A-Z_a-z]+", '"dev_value"', content)

    if fname == "main.py" and "import app" in content and "app = FastAPI()" not in content:
        content = re.sub(r"^import app\n", "", content, flags=re.MULTILINE)
        lines = content.split("\n")
        insert = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert = i + 1
        lines.insert(insert, "\napp = FastAPI()\n")
        content = "\n".join(lines)

    if fname == "main.py" and "Jinja2Templates" not in content and "templates" in content:
        templates_dir = "app/templates" if "app/" in path else "templates"
        content = content.replace("app = FastAPI()", f'app = FastAPI()\ntemplates = Jinja2Templates(directory="{templates_dir}")')

    return content

def fix_child_template(path: str, content: str) -> str:
    fname = os.path.basename(path)
    if fname == "base.html" or "templates/" not in path:
        return content

    if content.strip().startswith("{% extends"):
        block_count = content.count("{% block content %}")
        if block_count <= 1:
            return content
        parts = content.split("{% block content %}")
        return "{% extends 'base.html' %}\n{% block content %}" + parts[-1]

    body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)
    if body_match:
        inner = body_match.group(1).strip()
        inner = re.sub(r"\{%-?\s*block content\s*-?%\}.*?\{%-?\s*endblock\s*-?%\}", "", inner, count=1, flags=re.DOTALL).strip()
        return f"{{% extends 'base.html' %}}\n{{% block content %}}\n{inner}\n{{% endblock %}}"

    cleaned = re.sub(r"\{%-?\s*block content\s*-?%\}", "", content, count=1)
    cleaned = re.sub(r"\{%-?\s*endblock\s*-?%\}", "", cleaned, count=1)
    return f"{{% extends 'base.html' %}}\n{{% block content %}}\n{cleaned.strip()}\n{{% endblock %}}"
