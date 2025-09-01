import asyncio
import os
import platform
from urllib.parse import quote_plus
import httpx
import aiofiles
from functools import partial
from random import randint, uniform

# ============ CONFIG ============
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
DATA_FOLDER = "Data"
TRIGGER_FILE = r"Frontend\Files\ImageGeneration.data"

AUTO_OPEN_IMAGES = True  # True / False
REQUEST_TIMEOUT = 60
RETRY_ATTEMPTS = 3

# Ensure the Data folder exists
os.makedirs(DATA_FOLDER, exist_ok=True)

# ============ UTILITIES ============
def build_pollinations_url(prompt: str) -> str:
    """Return a safe Pollinations URL for the prompt."""
    return f"{POLLINATIONS_BASE}{quote_plus(prompt)}"

def open_image_nonblocking(path: str):
    """Open an image using the system's default viewer (non-blocking)."""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            os.system(f'open "{path}"')  # macOS
        else:
            os.system(f'xdg-open "{path}"')  # Linux
    except Exception as e:
        print(f"⚠️ Could not auto-open {path}: {e}")

def sync_write_file(path: str, content: bytes):
    """Blocking file write (used with run_in_executor for speed)."""
    with open(path, "wb") as f:
        f.write(content)

async def save_image(path: str, content: bytes):
    """Save image asynchronously (threaded write)."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, partial(sync_write_file, path, content))
    print(f"✅ Saved -> {path}")
    return path

# ============ IMAGE FETCH ============
async def fetch_image_bytes(url: str, client: httpx.AsyncClient, retries: int = RETRY_ATTEMPTS):
    """Fetch image bytes with retry + jitter backoff."""
    delay = 1.0
    for attempt in range(1, retries + 1):
        try:
            resp = await client.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt < retries:
                jitter = uniform(0.5, 1.5)
                print(f"⚠️ Fetch error {attempt}/{retries} for {url}: {e}. Retrying in {delay * jitter:.1f}s...")
                await asyncio.sleep(delay * jitter)
                delay *= 2
                continue
            else:
                print(f"❌ Failed to fetch image after {retries} attempts: {e}")
                return None
        except Exception as e:
            print(f"❌ Unexpected error fetching image: {e}")
            return None

async def generate_image(prompt: str, client: httpx.AsyncClient):
    """Generate a single image using Pollinations and save it."""
    url = build_pollinations_url(f"{prompt}, seed={randint(10000, 99999)}")
    content = await fetch_image_bytes(url, client)
    if not content:
        print("⚠️ No image was saved (request failed).")
        return

    safe_name = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in prompt).strip().replace(" ", "_")
    image_path = os.path.join(DATA_FOLDER, f"{safe_name}_1.png")

    saved_path = await save_image(image_path, content)

    if AUTO_OPEN_IMAGES:
        open_image_nonblocking(saved_path)

    print("✨ Done")

# ============ FILE WATCHER ============
async def watch_trigger_file(client: httpx.AsyncClient):
    """Watch the trigger file and run image generation when requested."""
    last_data = None
    while True:
        try:
            async with aiofiles.open(TRIGGER_FILE, "r") as f:
                data = await f.read()

            if data and data != last_data:
                last_data = data
                try:
                    prompt, status = data.split(",", 1)
                    status = status.strip().lower()
                    prompt = prompt.strip()

                    if status == "true" and prompt:
                        print("🚀 Generating Image (Pollinations)...")
                        asyncio.create_task(generate_image(prompt, client))

                        # Reset trigger file
                        async with aiofiles.open(TRIGGER_FILE, "w") as fw:
                            await fw.write("False, False")
                except ValueError:
                    pass  # Ignore bad format
        except FileNotFoundError:
            pass  # Wait until file exists
        except Exception as e:
            print(f"⚠️ Watcher error: {e}")

        await asyncio.sleep(0.5)

# ============ ENTRY POINT ============
async def main():
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    async with httpx.AsyncClient(limits=limits, timeout=REQUEST_TIMEOUT) as client:
        await watch_trigger_file(client)

if __name__ == "__main__":
    asyncio.run(main())
