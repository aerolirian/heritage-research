"""
Amazon scanner — competitor annotated edition analysis.
Signals: BSR movement, pricing, review velocity, description strategies.
A title in the top BSR with no strong annotated edition = underserved gap.
Uses Playwright (handles JS rendering and bot detection better than requests).
"""
from playwright.sync_api import sync_playwright
import re

SEARCH_QUERIES = [
    "annotated classics philosophy kindle",
    "philosophical edition public domain",
    "annotated thomas mann",
    "annotated kafka",
    "annotated dostoevsky",
    "annotated james joyce",
    "annotated tolstoy",
    "literary classics annotated introduction",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        for query in SEARCH_QUERIES:
            try:
                encoded = query.replace(" ", "+")
                page.goto(
                    f"https://www.amazon.com/s?k={encoded}&i=digital-text&rh=n%3A154606011",
                    timeout=20000,
                )
                page.wait_for_timeout(3000)

                results = page.evaluate("""
                    () => Array.from(document.querySelectorAll('[data-component-type="s-search-result"]'))
                    .slice(0, 10)
                    .map(el => ({
                        title: (el.querySelector('h2 a span') || {}).innerText || '',
                        author: (el.querySelector('.a-size-base.s-underline-text') || {}).innerText || '',
                        price: (el.querySelector('.a-price .a-offscreen') || {}).innerText || '',
                        rating: (el.querySelector('.a-icon-alt') || {}).innerText || '',
                        reviews: (el.querySelector('.a-size-small .a-link-normal') || {}).innerText || '',
                        bsr_badge: (el.querySelector('.a-badge-text') || {}).innerText || '',
                    }))
                    .filter(r => r.title.length > 2)
                """)

                for r in results:
                    title = r.get("title", "")
                    author = r.get("author", "")
                    bsr = r.get("bsr_badge", "")

                    # Flag as gap if Heritage Canon hasn't published this title yet
                    candidates.append({
                        "source": "amazon",
                        "title": title,
                        "author": author,
                        "amazon_price": r.get("price", ""),
                        "amazon_rating": r.get("rating", ""),
                        "amazon_reviews": r.get("reviews", ""),
                        "bsr_badge": bsr,
                        "search_query": query,
                        "why_now": f"Competitor annotated edition — {r.get('reviews','')} reviews, {r.get('price','')}",
                        "raw_score": 25 + (10 if bsr else 0),
                    })

            except Exception as e:
                print(f"  [amazon/{query[:30]}] {e}")

        ctx.close()
        browser.close()

    return candidates
