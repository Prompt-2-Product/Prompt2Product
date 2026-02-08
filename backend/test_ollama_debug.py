import requests
import sys

print("Sending request to Ollama...")
try:
    resp = requests.post('http://127.0.0.1:11434/api/chat', json={'model': 'qwen2.5-coder:7b', 'messages': [{'role': 'user', 'content': 'hi'}], 'stream': False}, timeout=10)
    print(f"Status: {resp.status_code}")
    print(resp.text[:200])
except Exception as e:
    print(f"Error: {e}")
