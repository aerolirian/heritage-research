"""
Tumblr scanner — active literary/philosophy community, especially European modernism.
Younger readers discovering Kafka, Mann, Woolf through aesthetic/meme culture.
Uses Tumblr API v2 (free, needs OAuth client credentials).
Falls back to Playwright scraping of public tag pages if no API key.
"""
import requests

TUMBLR_API = "https://api.tumblr.com/v2"

TAGS_TO_MONITOR = [
    "classic literature", "literary fiction", "philosophical fiction",
    "thomas mann", "franz kafka", "james joyce", "dostoevsky",
    "virginia woolf", "knut hamsun", "sinclair lewis",
    "modernist literature", "european literature", "annotated classics",
    "philosophy books", "existentialism", "nietzsche",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "woolf": "Virginia Woolf",
    "hemingway": "Ernest Hemingway", "fitzgerald": "F. Scott Fitzgerald",
}


def scan(config):
    api_key = config.get("tumblr_api_key", "")
    if api_key:
        return _scan_api(api_key)
    return _scan_playwright()


def _scan_api(api_key):
    candidates = []
    for tag in TAGS_TO_MONITOR:
        try:
            resp = requests.get(f"{TUMBLR_API}/tagged", params={
                "tag": tag,
                "api_key": api_key,
                "limit": 20,
            }, timeout=10)
            resp.raise_for_status()
            posts = resp.json().get("response", [])

            for post in posts:
                body = post.get("body", "") or post.get("caption", "") or ""
                title = post.get("title", "") or ""
                text = (title + " " + body).lower()
                notes = post.get("note_count", 0)

                for kw, full_name in AUTHOR_KEYWORDS.items():
                    if kw in text:
                        candidates.append({
                            "source": "tumblr",
                            "author": full_name,
                            "title": "",
                            "tumblr_tag": tag,
                            "tumblr_notes": notes,
                            "tumblr_url": post.get("post_url", ""),
                            "why_now": f"Tumblr #{tag}: {notes} notes",
                            "raw_score": min(40, 10 + notes / 50),
                        })
                        break
        except Exception as e:
            print(f"  [tumblr/{tag}] {e}")
    return candidates


def _scan_playwright():
    from playwright.sync_api import sync_playwright
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for tag in TAGS_TO_MONITOR[:8]:
            try:
                encoded = tag.replace(" ", "-")
                page.goto(f"https://www.tumblr.com/tagged/{encoded}", timeout=20000)
                page.wait_for_timeout(3000)

                posts = page.evaluate("""
                    () => Array.from(document.querySelectorAll('article, [data-id]'))
                    .slice(0, 15)
                    .map(el => ({
                        text: el.innerText.slice(0, 300),
                        notes: (el.querySelector('[class*="note"]') || {}).innerText || '0',
                    }))
                    .filter(p => p.text.length > 20)
                """)

                for post in posts:
                    text = post.get("text", "").lower()
                    for kw, full_name in AUTHOR_KEYWORDS.items():
                        if kw in text:
                            candidates.append({
                                "source": "tumblr",
                                "author": full_name,
                                "title": "",
                                "tumblr_tag": tag,
                                "tumblr_notes": post.get("notes", "0"),
                                "why_now": f"Tumblr #{tag} activity",
                                "raw_score": 20,
                            })
                            break
            except Exception as e:
                print(f"  [tumblr_playwright/{tag}] {e}")

        browser.close()

    return candidates
