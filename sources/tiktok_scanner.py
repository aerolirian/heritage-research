"""
TikTok/BookTok scanner — which PD editions are getting organic traction,
what angles and aesthetics are performing, comment sentiment.
Uses Playwright (JS-rendered). Scrapes public pages only, no login required.
"""
from playwright.sync_api import sync_playwright
import re

BOOKTOK_SEARCHES = [
    "booktok classics",
    "annotated classics booktok",
    "philosophical novel booktok",
    "thomas mann booktok",
    "kafka booktok",
    "joyce ulysses booktok",
    "dostoevsky booktok",
    "public domain books tiktok",
    "classic literature tiktok 2025",
]

AUTHOR_KEYWORDS = [
    "mann", "kafka", "joyce", "dostoevsky", "tolstoy", "hamsun",
    "hemingway", "fitzgerald", "woolf", "lewis", "conrad", "flaubert",
    "chekhov", "zola", "hardy", "dickens", "hugo",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
            viewport={"width": 390, "height": 844},
        )
        page = ctx.new_page()

        for query in BOOKTOK_SEARCHES:
            try:
                encoded = query.replace(" ", "%20")
                page.goto(f"https://www.tiktok.com/search?q={encoded}", timeout=20000)
                page.wait_for_timeout(3000)

                # Extract video titles/descriptions visible on search results
                texts = page.evaluate("""
                    () => Array.from(document.querySelectorAll('[data-e2e="search-card-desc"], .tiktok-j2DY66-DivWrapper, span[class*="desc"]'))
                         .map(el => el.innerText).filter(t => t.length > 10)
                """)

                for text in texts:
                    text_lower = text.lower()
                    for author in AUTHOR_KEYWORDS:
                        if author in text_lower:
                            candidates.append({
                                "source": "tiktok",
                                "author": author.title(),
                                "title": "",
                                "tiktok_query": query,
                                "tiktok_text": text[:200],
                                "why_now": f"BookTok discussion: '{text[:80].strip()}'",
                                "raw_score": 40,
                            })
                            break
            except Exception as e:
                print(f"  [tiktok/{query[:30]}] {e}")

        ctx.close()
        browser.close()

    return candidates
