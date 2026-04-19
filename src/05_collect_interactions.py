import asyncio
import csv
import os
import re
import random
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

INPUT_FILE = "filtered_data/metadata_keep_url.txt"
OUTPUT_FILE = "filtered_data/video_interactions.csv"

DETAIL_API_KEYWORD = "aweme/v1/web/aweme/detail"
VIDEO_ID_REGEX = re.compile(r"video/(\d+)")


def parse_video_id(url: str) -> Optional[str]:
    match = VIDEO_ID_REGEX.search(url)
    return match.group(1) if match else None


def to_int(value) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        s = value.strip().replace(",", "")
        if s.isdigit():
            return int(s)
    return None


def pick_stat(stats: Dict[str, Any], *keys: str) -> Optional[int]:
    for key in keys:
        val = stats.get(key)
        parsed = to_int(val)
        if parsed is not None:
            return parsed
    return None


async def collect_interactions():
    """
    Collect engagement statistics for filtered Douyin videos.

    Extracted fields:
    - digg_count (likes)
    - comment_count
    - collect_count (favorites)
    - share_count

    Uses:
    1. API interception (primary)
    2. DOM fallback (secondary)
    """

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"[ERROR] Input file not found: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if "douyin.com/video/" in line.strip()]

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u.count("https://") > 1:
            u = "https://" + u.split("https://")[-1]
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    stats_map: Dict[str, Dict[str, Any]] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
            )
        )
        page = await context.new_page()

        async def handle_response(response):
            if DETAIL_API_KEYWORD in response.url:
                try:
                    data = await response.json()
                    item = (data or {}).get("aweme_detail", {}) or {}
                    video_id = item.get("aweme_id")
                    if not video_id:
                        return

                    stats = item.get("statistics", {}) or {}

                    digg = pick_stat(stats, "digg_count", "like_count")
                    comment = pick_stat(stats, "comment_count")
                    collect = pick_stat(stats, "collect_count", "favorite_count")
                    share = pick_stat(stats, "share_count", "forward_count", "repost_count")

                    stats_map[video_id] = {
                        "digg_count": digg,
                        "comment_count": comment,
                        "collect_count": collect,
                        "share_count": share,
                        "source": "detail_json",
                    }
                except Exception:
                    pass

        page.on("response", handle_response)

        # Step 1: Manual login
        await page.goto("https://www.douyin.com/")
        print("\n[IMPORTANT] Please scan QR code to log in.")
        print("Press ENTER after login.")
        await asyncio.to_thread(input)

        # Prepare output
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        file_exists = os.path.exists(OUTPUT_FILE)

        f_out = open(OUTPUT_FILE, "a", newline="", encoding="utf-8-sig")
        writer = csv.writer(f_out)

        if (not file_exists) or os.path.getsize(OUTPUT_FILE) == 0:
            writer.writerow([
                "video_id", "url",
                "digg_count", "comment_count", "collect_count", "share_count",
                "status_note", "source"
            ])

        # Step 2: Iterate videos
        for i, url in enumerate(unique_urls):
            video_id = parse_video_id(url)

            if not video_id:
                writer.writerow(["", url, "", "", "", "", "invalid_url", ""])
                f_out.flush()
                continue

            print(f"[PROCESS] {i+1}/{len(unique_urls)} | {video_id}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                found = False
                for _ in range(10):
                    await asyncio.sleep(1)
                    if video_id in stats_map:
                        s = stats_map[video_id]
                        writer.writerow([
                            video_id, url,
                            s.get("digg_count", ""),
                            s.get("comment_count", ""),
                            s.get("collect_count", ""),
                            s.get("share_count", ""),
                            "ok",
                            s.get("source", "detail_json"),
                        ])
                        found = True
                        break

                # Fallback: DOM extraction
                if not found:
                    digg = comment = collect = share = None

                    try:
                        await page.wait_for_timeout(1500)
                        candidates = await page.locator(
                            "text=/^\\d+(\\.\\d+)?[KkWw]?$|^\\d{1,3}(,\\d{3})+$/"
                        ).all_inner_texts()

                        cleaned = [t.strip() for t in candidates if t.strip()]

                        if len(cleaned) >= 4:
                            def parse_human_num(s: str) -> Optional[int]:
                                s = s.replace(",", "")
                                m = re.match(r"^(\d+(?:\.\d+)?)([KkWw])?$", s)
                                if not m:
                                    return int(s) if s.isdigit() else None
                                num = float(m.group(1))
                                suf = (m.group(2) or "").lower()
                                if suf == "k":
                                    return int(num * 1000)
                                if suf == "w":
                                    return int(num * 10000)
                                return int(num)

                            digg = parse_human_num(cleaned[0])
                            comment = parse_human_num(cleaned[1])
                            collect = parse_human_num(cleaned[2])
                            share = parse_human_num(cleaned[3])

                    except Exception:
                        pass

                    writer.writerow([
                        video_id, url,
                        digg or "",
                        comment or "",
                        collect or "",
                        share or "",
                        "fallback_dom",
                        "fallback",
                    ])

                f_out.flush()
                await asyncio.sleep(random.uniform(0.6, 1.2))

            except Exception:
                writer.writerow([video_id, url, "", "", "", "", "timeout", ""])
                f_out.flush()
                await asyncio.sleep(random.uniform(1.0, 2.0))

        f_out.close()
        await browser.close()

    print(f"\n[SUCCESS] Interaction data saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(collect_interactions())
