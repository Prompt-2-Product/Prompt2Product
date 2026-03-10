import httpx
import asyncio

async def test():
    base_url = "http://127.0.0.1:11435"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{base_url}/api/tags")
            print("--- Tags ---")
            print(res.text)
            print("------------")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
