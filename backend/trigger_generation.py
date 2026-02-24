import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def create_project(name):
    print(f"Creating project '{name}'...")
    resp = requests.post(f"{BASE_URL}/projects", json={"name": name})
    if resp.status_code != 200:
        print(f"Failed to create project: {resp.text}")
        sys.exit(1)
    return resp.json()

def start_run(project_id, prompt):
    print(f"Starting run for project {project_id}...")
    payload = {
        "prompt": prompt,
        "entrypoint": "main.py" 
    }
    resp = requests.post(f"{BASE_URL}/projects/{project_id}/runs", json=payload)
    if resp.status_code != 200:
        print(f"Failed to start run: {resp.text}")
        sys.exit(1)
    return resp.json()

def monitor_run(run_id):
    print(f"Monitoring run {run_id}...")
    last_log_count = 0
    while True:
        resp = requests.get(f"{BASE_URL}/runs/{run_id}/logs")
        if resp.status_code == 200:
            logs = resp.json()
            if len(logs) > last_log_count:
                for log in logs[last_log_count:]:
                    # Use .get to be safe, defaulting to INFO if keys missing
                    level = log.get('level', 'INFO')
                    stage = log.get('stage', 'UNKNOWN')
                    message = log.get('message', '')
                    print(f"[{stage.upper()}:{level.upper()}] {message}")
                last_log_count = len(logs)
            
            # Check status
            run_resp = requests.get(f"{BASE_URL}/runs/{run_id}")
            status = run_resp.json()['status']
            if status in ['success', 'failed']:
                print(f"Run finished with status: {status}")
                break
        time.sleep(2)

if __name__ == "__main__":
    prompt = "Create a modern personal finance dashboard (SpendWise) to track expenses, visualize budget with charts, and manage savings goals. Use a dark theme with neon accents."
    
    try:
        project = create_project("DeepSeek Demo")
        project_id = project['id']
        print(f"Project ID: {project_id}")
        
        run = start_run(project_id, prompt)
        run_id = run['run_id']
        print(f"Run ID: {run_id}")
        
        monitor_run(run_id)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to backend. Is it running?")
