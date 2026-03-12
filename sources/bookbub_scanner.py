"""
BookBub scanner — 15M+ readers, editorial picks signal commercial literary demand.
Deal pages are server-rendered HTML — no Playwright needed.
Uses requests + BeautifulSoup directly against /ebook-deals genre pages.
"""
import requests
from bs4 import BeautifulSoup

BASE = "https://www.bookbub.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

GENRE_PAGES = [
    f"{BASE}/ebook-deals?genre=literary+fiction",
    f"{BASE}/ebook-deals?genre=classics",
    f"{BASE}/ebook-deals?genre=historical+fiction",
    f"{BASE}/ebook-deals?genre=philosophy",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "hardy": "Thomas Hardy",
    "dickens": "Charles Dickens", "hugo": "Victor Hugo",
}


def scan(config):
    candidates = []

    for url in GENRE_PAGES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            for book in soup.select("[class*='BookCard'], [class*='book-card'], article"):
                title_el = book.select_one("[class*='title'], h2, h3")
                author_el = book.select_one("[class*='author']")
                price_el = book.select_one("[class*='price'], [class*='deal']")

                title = title_el.get_text(strip=True) if title_el else ""
                author = author_el.get_text(strip=True) if author_el else ""
                price = price_el.get_text(strip=True) if price_el else ""

                combined = (title + " " + author).lower()
                for kw, full_name in AUTHOR_KEYWORDS.items():
                    if kw in combined:
                        candidates.append({
                            "source": "bookbub",
                            "author": full_name,
                            "title": title,
                            "bookbub_author": author,
                            "bookbub_price": price,
                            "bookbub_url": url,
                            "why_now": f"BookBub deal: '{title}' at {price} — editorial pick for 15M readers",
                            "raw_score": 35,
                        })
                        break

        except Exception as e:
            print(f"  [bookbub/{url}] {e}")

    return candidates
