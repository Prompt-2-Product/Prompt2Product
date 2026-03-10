import httpx
import asyncio
import sys

async def test():
    url = "http://127.0.0.1:11435/api/tags"
    print(f"Connecting to {url}...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url)
            print(f"Status Code: {res.status_code}")
            if res.status_code == 200:
                print("Models found:")
                data = res.json()
                for m in data.get('models', []):
                    print(f" - {m['name']}")
            else:
                print(f"Error body: {res.text}")
    except Exception as e:
        print(f"Connection failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
