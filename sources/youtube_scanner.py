"""
YouTube scanner — literary/philosophical video essays.
Video essay treatment of a classic = intellectual resurgence signal.
Channels like Wisecrack, Like Stories of Old, Einzelgänger, Shaun, Philosophy Overdose,
or even mainstream channels covering a PD author = exact Heritage Canon audience.
Uses YouTube Data API v3 (free, 10,000 units/day quota).
Falls back to scraping search results via Playwright if no API key.
"""
import requests
from datetime import date, timedelta

YT_API = "https://www.googleapis.com/youtube/v3"

SEARCH_QUERIES = [
    "thomas mann video essay",
    "franz kafka analysis",
    "james joyce ulysses explained",
    "dostoevsky philosophy",
    "classic literature video essay 2024 2025",
    "annotated classics philosophy",
    "knut hamsun",
    "sinclair lewis babbitt",
    "fitzgerald gatsby meaning",
    "virginia woolf stream of consciousness",
    "nietzsche novel",
    "tolstoy war peace meaning",
    "public domain classic philosophy analysis",
]


def scan(config):
    api_key = config.get("youtube_api_key", "")
    if api_key:
        return _scan_api(api_key)
    else:
        return _scan_playwright()


def _scan_api(api_key):
    candidates = []
    cutoff = (date.today() - timedelta(days=180)).strftime("%Y-%m-%dT00:00:00Z")

    for query in SEARCH_QUERIES:
        try:
            resp = requests.get(f"{YT_API}/search", params={
                "key": api_key,
                "q": query,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": cutoff,
                "maxResults": 10,
                "part": "snippet",
            }, timeout=10)
            resp.raise_for_status()
            items = resp.json().get("items", [])

            for item in items:
                snippet = item.get("snippet", {})
                title = snippet.get("title", "")
                channel = snippet.get("channelTitle", "")
                desc = snippet.get("description", "")[:200]
                vid_id = item.get("id", {}).get("videoId", "")
                pub_date = snippet.get("publishedAt", "")[:10]

                candidates.append({
                    "source": "youtube",
                    "author": _extract_author(title + " " + desc),
                    "title": "",
                    "yt_title": title,
                    "yt_channel": channel,
                    "yt_url": f"https://youtu.be/{vid_id}",
                    "yt_published": pub_date,
                    "search_query": query,
                    "why_now": f"Video essay: '{title[:70]}' by {channel}",
                    "raw_score": 45,
                })
        except Exception as e:
            print(f"  [youtube/{query[:30]}] {e}")

    return candidates


def _scan_playwright():
    """Fallback: scrape YouTube search results."""
    from playwright.sync_api import sync_playwright
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for query in SEARCH_QUERIES[:6]:  # limit to avoid long runtime
            try:
                encoded = query.replace(" ", "+")
                page.goto(f"https://www.youtube.com/results?search_query={encoded}", timeout=20000)
                page.wait_for_timeout(3000)

                results = page.evaluate("""
                    () => Array.from(document.querySelectorAll('ytd-video-renderer #video-title'))
                    .slice(0, 8)
                    .map(el => ({ title: el.innerText, href: el.href }))
                """)

                for r in results:
                    t = r.get("title", "")
                    if not t:
                        continue
                    candidates.append({
                        "source": "youtube",
                        "author": _extract_author(t),
                        "title": "",
                        "yt_title": t,
                        "yt_url": r.get("href", ""),
                        "search_query": query,
                        "why_now": f"Video essay: '{t[:70]}'",
                        "raw_score": 35,
                    })
            except Exception as e:
                print(f"  [youtube_playwright/{query[:30]}] {e}")

        browser.close()

    return candidates


AUTHOR_MAP = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "nietzsche": "Friedrich Nietzsche",
    "flaubert": "Gustave Flaubert", "chekhov": "Anton Chekhov",
}


def _extract_author(text):
    text_lower = text.lower()
    for key, full in AUTHOR_MAP.items():
        if key in text_lower:
            return full
    return ""
