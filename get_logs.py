import sys
import os
import sqlite3

db_path = "d:/FYP/backend/app.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get latest run
cursor.execute("SELECT id, status, project_id FROM run ORDER BY id DESC LIMIT 1")
run = cursor.fetchone()
if run:
    run_id, status, project_id = run
    print(f"Latest Run ID: {run_id}, Status: {status}, Project ID: {project_id}")
    
    # Get logs from logevent table
    cursor.execute("SELECT stage, message FROM logevent WHERE run_id = ? ORDER BY id ASC", (run_id,))
    logs = cursor.fetchall()
    for stage, message in logs:
        print(f"[{stage}] {message}")
else:
    print("No runs found")

conn.close()
