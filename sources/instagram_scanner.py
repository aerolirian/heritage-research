"""
Instagram scanner — which PD/annotated editions are getting traction,
what cover aesthetics perform, Heritage Canon aesthetic vs competitors.
Scrapes public hashtag pages via Playwright. No login required for public tags.
"""
from playwright.sync_api import sync_playwright

HASHTAGS = [
    "booktok",
    "classicbooks",
    "annotatedbooks",
    "philosophicalfiction",
    "literarybooks",
    "bookstagram",
    "classiclit",
    "canonbooks",
    "greatliterature",
]

AUTHOR_KEYWORDS = [
    "mann", "kafka", "joyce", "dostoevsky", "tolstoy", "hamsun",
    "hemingway", "fitzgerald", "woolf", "lewis", "flaubert",
    "chekhov", "dickens", "hugo", "zola",
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

        for tag in HASHTAGS:
            try:
                page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=20000)
                page.wait_for_timeout(3000)

                # Extract alt text and captions from public posts
                texts = page.evaluate("""
                    () => Array.from(document.querySelectorAll('img[alt], ._aagv img'))
                         .map(el => el.getAttribute('alt') || '')
                         .filter(t => t.length > 10)
                """)

                for text in texts:
                    text_lower = text.lower()
                    for author in AUTHOR_KEYWORDS:
                        if author in text_lower:
                            candidates.append({
                                "source": "instagram",
                                "author": author.title(),
                                "title": "",
                                "hashtag": tag,
                                "caption": text[:200],
                                "why_now": f"Instagram #{tag} traction: '{text[:60].strip()}'",
                                "raw_score": 30,
                            })
                            break
            except Exception as e:
                print(f"  [instagram/#{tag}] {e}")

        ctx.close()
        browser.close()

    return candidates
