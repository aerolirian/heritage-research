"""
Five Books scanner — expert curated reading lists (academics, writers, thinkers).
"Best books on existentialism", "Best novels about bureaucracy", etc.
Signal: experts articulate exactly why a book matters — best subtitle angle source.

Pages are server-rendered HTML with Schema.org JSON-LD embedded — no Playwright needed.
Uses requests + BeautifulSoup. Much faster and more reliable than Playwright.
"""
import json
import requests
from bs4 import BeautifulSoup

BASE = "https://fivebooks.com"
HEADERS = {
    "User-Agent": "heritage-research/1.0 (https://github.com/aerolirian/heritage-research)"
}

CATEGORY_PAGES = [
    f"{BASE}/best-books/philosophy/",
    f"{BASE}/best-books/literary-fiction/",
    f"{BASE}/best-books/history-of-ideas/",
    f"{BASE}/best-books/classic-literature/",
    f"{BASE}/best-books/philosophy-of-mind/",
    f"{BASE}/best-books/european-history/",
    f"{BASE}/best-books/20th-century-history/",
    f"{BASE}/best-books/existentialism/",
    f"{BASE}/best-books/modernism/",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "nietzsche": "Friedrich Nietzsche",
    "camus": "Albert Camus", "rilke": "Rainer Maria Rilke",
    "musil": "Robert Musil", "broch": "Hermann Broch",
    "zola": "Emile Zola", "hardy": "Thomas Hardy",
}


def scan(config):
    candidates = []
    seen = set()

    # Get interview links from each category
    interview_urls = []
    for cat_url in CATEGORY_PAGES:
        try:
            resp = requests.get(cat_url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.select("a[href*='/interviews/']"):
                href = a["href"]
                if not href.startswith("http"):
                    href = BASE + href
                if href not in seen:
                    seen.add(href)
                    interview_urls.append(href)
        except Exception as e:
            print(f"  [fivebooks/category] {e}")

    # Scrape each interview for recommended books
    for url in interview_urls[:60]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")

            # Extract JSON-LD schema data if present
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("@type") in ("Book", "ItemList"):
                            # Extract book recommendations
                            pass
                except Exception:
                    pass

            # Extract expert name
            expert_el = soup.select_one(".interviewer-name, .expert-name, [class*='expert']")
            expert = expert_el.get_text(strip=True) if expert_el else ""

            # Extract recommended book titles and authors
            book_els = soup.select(".book-recommendation, .recommended-book, [class*='book-title']")
            for book_el in book_els:
                title_el = book_el.select_one("h3, h4, .title")
                author_el = book_el.select_one(".author, [class*='author']")
                book_title = title_el.get_text(strip=True) if title_el else ""
                book_author = author_el.get_text(strip=True) if author_el else ""

                combined = (book_title + " " + book_author).lower()
                for kw, full_name in AUTHOR_KEYWORDS.items():
                    if kw in combined:
                        candidates.append({
                            "source": "fivebooks",
                            "author": full_name,
                            "title": book_title,
                            "fivebooks_expert": expert,
                            "fivebooks_url": url,
                            "why_now": f"Expert recommended on Five Books: '{book_title}' (by {expert or 'expert'})",
                            "raw_score": 40,
                        })
                        break

        except Exception as e:
            print(f"  [fivebooks/interview] {e}")

    return candidates
