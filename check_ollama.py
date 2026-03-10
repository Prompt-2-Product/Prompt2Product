import socket
def check(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        try:
            s.connect(('127.0.0.1', port))
            print(f"Port {port} is open")
        except Exception as e:
            print(f"Port {port} is closed: {e}")

print("Checking Ollama ports...")
check(11434)
check(11435)
