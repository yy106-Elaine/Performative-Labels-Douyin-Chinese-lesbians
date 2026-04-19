import asyncio
import csv
import re
import os
from playwright.async_api import async_playwright

INPUT_FILE = "urls.txt"
OUTPUT_FILE = "existing_videos_metadata.csv"


async def extract_video_metadata():
    """
    Extract metadata for Douyin video URLs by intercepting
    the aweme detail API response.

    For each video URL, the script captures:
    - video ID
    - full caption / description
    - extracted hashtags
    """

    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if "douyin.com/video/" in line]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Store intercepted metadata by video ID
        metadata_map = {}

        async def handle_response(response):
            """
            Intercept Douyin video detail API responses and
            extract description and hashtag metadata.
            """
            if "aweme/v1/web/aweme/detail" in response.url:
                try:
                    json_data = await response.json()
                    item = json_data.get("aweme_detail", {})
                    video_id = item.get("aweme_id")
                    desc = item.get("desc", "")
                    tags = [
                        t.get("hashtag_name")
                        for t in item.get("text_extra", [])
                        if t.get("hashtag_name")
                    ]
                    metadata_map[video_id] = {
                        "desc": desc,
                        "tags": ",".join(tags),
                    }
                except Exception:
                    pass

        page.on("response", handle_response)

        # Step 1: Manual login
        await page.goto("https://www.douyin.com/")
        print("\n[IMPORTANT] Please scan the QR code to log in.")
        print("After logging in successfully, return here and press ENTER to continue.")
        await asyncio.to_thread(input)

        # Step 2: Prepare output file
        file_exists = os.path.exists(OUTPUT_FILE)
        file_is_empty = (not file_exists) or os.path.getsize(OUTPUT_FILE) == 0

        f_out = open(OUTPUT_FILE, "a", newline="", encoding="utf-8-sig")
        writer = csv.writer(f_out)

        if file_is_empty:
            writer.writerow(["video_id", "url", "full_caption", "extracted_hashtags"])

        # Step 3: Visit each URL and extract metadata
        for i, url in enumerate(urls):
            # Fix malformed lines that accidentally contain multiple https:// prefixes
            if url.count("https://") > 1:
                url = "https://" + url.split("https://")[-1]

            video_id_match = re.search(r"video/(\d+)", url)
            if not video_id_match:
                continue

            video_id = video_id_match.group(1)
            print(f"[REQUEST] [{i + 1}/{len(urls)}] Processing video: {video_id}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)

                # Wait up to 6 seconds for intercepted JSON data
                found = False
                for _ in range(3):
                    await asyncio.sleep(2)
                    data = metadata_map.get(video_id)
                    if data:
                        writer.writerow([video_id, url, data["desc"], data["tags"]])
                        print(f"[SUCCESS] Captured metadata: {data['desc'][:30]}...")
                        found = True
                        break

                if not found:
                    title = await page.title()
                    writer.writerow([video_id, url, f"JSON not captured (page title: {title})", ""])
                    print("[WARNING] Failed to intercept metadata response.")

                f_out.flush()

            except Exception:
                print(f"[ERROR] Timeout or failed access for video: {video_id}")

        f_out.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(extract_video_metadata())
