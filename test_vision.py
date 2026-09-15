import httpx
import json
import asyncio

# Create a tiny 1x1 red pixel image as base64
tiny_red_pixel_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

payload = {
    "model": "gemma4:12b",
    "prompt": "What color is this image?",
    "images": [tiny_red_pixel_b64],
    "stream": False
}

async def run():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:11434/api/generate", json=payload, timeout=20.0)
            if response.status_code == 200:
                print("SUCCESS:", response.json().get("response"))
            else:
                print("FAILED:", response.text)
    except Exception as e:
        print("ERROR:", str(e))

asyncio.run(run())
