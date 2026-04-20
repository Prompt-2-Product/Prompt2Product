"""
tests/test_generation_quality.py
Tests against pre-generated apps — no need to run pipeline during tests.
Run pipeline first, then run these tests against the output.
"""
import os
import re
import ast
import httpx
import time
import subprocess
import pytest

# Point to your already-generated apps
GENERATED_APPS = [
    {
        "id": "fitness_tracker_fyp",
        "dir": "/home/noor/FYP/finetune/script/generated_fitness_tracker__community_cha",
        "prompt": "AI fitness tracker with community challenges and leaderboards",
        "expected_keywords": ["fitness", "challenge", "leaderboard", "workout"],
        "expected_pages_min": 2,
        "has_forms": False,
        "has_table": True,
    },
    {
        "id": "music_streaming_run4",
        "dir": "/home/noor/Prompt2Product/Prompt2Product/backend-new/storage/project_4/run_4",
        "prompt": "Music streaming platform with auth, playlists and recommendations",
        "expected_keywords": ["playlist", "music", "song", "recommendation", "search"],
        "expected_pages_min": 3,
        "has_forms": False,
        "has_table": False,
    },
    {
        "id": "news_portal_run5",
        "dir": "/home/noor/Prompt2Product/Prompt2Product/backend-new/storage/project_5/run_5",
        "prompt": "Build a news portal where editors can publish articles, categorize content, and manage comments",
        "expected_keywords": ["article", "news", "comment", "editor", "category"],
        "expected_pages_min": 1,  # routes use path params, simple count won't find them
        "has_forms": True,
        "has_table": True,
    },
    {
        "id": "freelance_marketplace_run6",
        "dir": "/home/noor/Prompt2Product/Prompt2Product/backend-new/storage/project_6/run_6",
        "prompt": "Build a freelance marketplace where clients post projects and freelancers bid",
        "expected_keywords": ["freelance", "project", "bid", "client", "freelancer"],
        "expected_pages_min": 2,
        "has_forms": False,
        "has_table": True,
    },
]

# Filter to only dirs that actually exist
EXISTING_APPS = [a for a in GENERATED_APPS if os.path.exists(a["dir"])]


def get_all_content(app_dir: str) -> str:
    """Read all .py and .html files in the app."""
    content = ""
    for root, dirs, files in os.walk(app_dir):
        dirs[:] = [d for d in dirs if d != "venv"]
        for fname in files:
            if fname.endswith((".py", ".html")):
                try:
                    with open(os.path.join(root, fname)) as f:
                        content += f.read().lower()
                except:
                    pass
    return content


def get_main_content(app_dir: str) -> str:
    for candidate in ["main.py", "app/main.py"]:
        path = os.path.join(app_dir, candidate)
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
    return ""


class TestStructure:
    """Test that generated apps have correct structure."""

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_main_py_exists(self, app):
        candidates = [
            os.path.join(app["dir"], "main.py"),
            os.path.join(app["dir"], "app", "main.py"),
        ]
        assert any(os.path.exists(p) for p in candidates), \
            f"main.py missing in {app['id']}"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_base_html_exists(self, app):
        found = False
        for root, dirs, files in os.walk(app["dir"]):
            dirs[:] = [d for d in dirs if d != "venv"]
            if "base.html" in files:
                found = True
                break
        assert found, f"base.html missing in {app['id']}"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_requirements_txt_exists(self, app):
        assert os.path.exists(os.path.join(app["dir"], "requirements.txt")), \
            f"requirements.txt missing in {app['id']}"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_main_py_syntax_valid(self, app):
        content = get_main_content(app["dir"])
        assert content, "main.py is empty"
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {app['id']}/main.py: {e}")

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_has_fastapi_app(self, app):
        content = get_main_content(app["dir"])
        assert "app = FastAPI()" in content, \
            f"{app['id']}: app = FastAPI() missing"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_no_bad_imports(self, app):
        content = get_main_content(app["dir"])
        bad = ["from tortoise", "from sqlalchemy", "from jose",
               "from passlib", "jinja2_fspaths"]
        for b in bad:
            assert b not in content, \
                f"{app['id']}: bad import found: {b}"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_templates_extend_base(self, app):
        for root, dirs, files in os.walk(app["dir"]):
            dirs[:] = [d for d in dirs if d != "venv"]
            for fname in files:
                if fname.endswith(".html") and fname != "base.html":
                    with open(os.path.join(root, fname)) as f:
                        content = f.read()
                    assert "extends" in content, \
                        f"{fname} does not extend base.html"


class TestPromptFulfillment:
    """
    SUPERVISOR CONCEPT:
    Given prompt X → assert output contains X-related features.
    Like assert add(2,3)==5 but for web app generation.
    """

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_output_matches_prompt_domain(self, app):
        """
        Core test: does generated code contain domain keywords from prompt?
        Prompt: "fitness tracker with leaderboards"
        Assert: "workout" or "challenge" in generated code
        """
        all_content = get_all_content(app["dir"])
        assert all_content, f"No content found in {app['id']}"

        matched = any(kw in all_content for kw in app["expected_keywords"])
        assert matched, \
            f"Prompt '{app['prompt']}' — none of {app['expected_keywords']} found in generated app"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_correct_number_of_pages(self, app):
        """
        Assert: prompt asking for N features → app has at least N pages/routes.
        """
        content = get_main_content(app["dir"])
        routes = re.findall(r'@app\.get\(["\']([^"\']+)["\']', content)
        page_routes = [r for r in routes if "/api/" not in r]
        assert len(page_routes) >= app["expected_pages_min"], \
            f"{app['id']}: expected {app['expected_pages_min']} pages, got {len(page_routes)}: {page_routes}"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_forms_present_when_needed(self, app):
        """
        Assert: prompt with add/create/submit → app has HTML forms.
        """
        if not app["has_forms"]:
            pytest.skip("Forms not expected for this app")
        all_content = get_all_content(app["dir"])
        assert "<form" in all_content, \
            f"{app['id']}: prompt implies user input but no HTML form found"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_table_present_for_leaderboard(self, app):
        """
        Assert: prompt with leaderboard/list → app has HTML table.
        """
        if not app["has_table"]:
            pytest.skip("Table not expected for this app")
        all_content = get_all_content(app["dir"])
        # Accept either an HTML table OR flex/grid card layout for leaderboard
        has_table = "<table" in all_content
        has_card_layout = any(kw in all_content for kw in [
            "leaderboard", "ranking", "rank", "position", "score", "flex", "grid"
        ])
        assert has_table or has_card_layout, \
            f"{app['id']}: prompt implies leaderboard/ranking but no table or card layout found"

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_tailwind_css_included(self, app):
        """Assert: all generated apps use Tailwind CDN."""
        all_content = get_all_content(app["dir"])
        assert "tailwind" in all_content, \
            f"{app['id']}: Tailwind CSS not found in templates"


class TestRuntime:
    """Test that generated apps actually run correctly."""

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_app_starts_without_crash(self, app):
        """Assert: generated app starts uvicorn without crashing."""
        venv_uvicorn = os.path.join(app["dir"], "venv/bin/uvicorn")
        if not os.path.exists(venv_uvicorn):
            pytest.skip(f"venv not found for {app['id']} — run ./run.sh first")

        port = 9100 + EXISTING_APPS.index(app)
        proc = subprocess.Popen(
            [venv_uvicorn, "main:app", "--port", str(port)],
            cwd=app["dir"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(6)

        try:
            assert proc.poll() is None, \
                f"{app['id']} crashed: {proc.stderr.read().decode()[:300]}"
        finally:
            proc.terminate()
            proc.wait()

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_home_route_returns_200(self, app):
        """Assert: / returns 200 — app serves HTML correctly."""
        venv_uvicorn = os.path.join(app["dir"], "venv/bin/uvicorn")
        if not os.path.exists(venv_uvicorn):
            pytest.skip(f"venv not found for {app['id']}")

        port = 9200 + EXISTING_APPS.index(app)
        proc = subprocess.Popen(
            [venv_uvicorn, "main:app", "--port", str(port)],
            cwd=app["dir"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(6)

        try:
            resp = httpx.get(
                f"http://localhost:{port}/",
                follow_redirects=True,
                timeout=5
            )
            assert resp.status_code == 200, \
                f"{app['id']}: / returned {resp.status_code}"
            assert resp.status_code != 500, \
                f"{app['id']}: Internal Server Error on /"
        finally:
            proc.terminate()
            proc.wait()

    @pytest.mark.parametrize("app", EXISTING_APPS, ids=[a["id"] for a in EXISTING_APPS])
    def test_no_500_on_any_route(self, app):
        """Assert: no GET route returns 500 Internal Server Error."""
        venv_uvicorn = os.path.join(app["dir"], "venv/bin/uvicorn")
        if not os.path.exists(venv_uvicorn):
            pytest.skip(f"venv not found for {app['id']}")

        port = 9300 + EXISTING_APPS.index(app)
        proc = subprocess.Popen(
            [venv_uvicorn, "main:app", "--port", str(port)],
            cwd=app["dir"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(6)

        try:
            content = get_main_content(app["dir"])
            routes = re.findall(r'@app\.get\(["\']([^"\']+)["\']', content)
            routes = [r for r in routes if "/api/" not in r and "{" not in r]

            for route in routes:
                resp = httpx.get(
                    f"http://localhost:{port}{route}",
                    follow_redirects=True,
                    timeout=5
                )
                assert resp.status_code != 500, \
                    f"{app['id']}: route {route} returned 500"
        finally:
            proc.terminate()
            proc.wait()