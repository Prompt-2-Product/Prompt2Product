from app.db.database import get_db

def create_project(name: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO projects (name) VALUES (?)", (name,))
    project_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"id": project_id, "name": name}

def list_projects():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"]} for r in rows]

def create_run(project_id: int, entrypoint: str = "app.main:app"):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO runs (project_id, entrypoint) VALUES (?, ?)", (project_id, entrypoint))
    run_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"id": run_id, "project_id": project_id, "status": "pending", "attempts": 0}

def get_run(run_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def update_run_status(run_id: int, status: str, attempts: int = None):
    conn = get_db()
    c = conn.cursor()
    if attempts is not None:
        c.execute("UPDATE runs SET status = ?, attempts = ? WHERE id = ?", (status, attempts, run_id))
    else:
        c.execute("UPDATE runs SET status = ? WHERE id = ?", (status, run_id))
    conn.commit()
    conn.close()

def log_message(run_id: int, stage: str, message: str, level: str = 'INFO'):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO logs (run_id, stage, level, message) VALUES (?, ?, ?, ?)", (run_id, stage, level, message))
    conn.commit()
    conn.close()

def list_logs(run_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT stage, level, message, timestamp FROM logs WHERE run_id = ? ORDER BY id ASC", (run_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
