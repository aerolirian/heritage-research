"""
LibraryThing scanner — serious literary readers and catalogers.
More academic and literary than Goodreads. Strong signal for canonical works.

Uses LibraryThing's free REST API directly (no wrapper needed — simple enough).
Register for a free key at: https://www.librarything.com/api
Falls back to requests + BeautifulSoup for list pages (server-rendered HTML).
"""
import requests
from bs4 import BeautifulSoup

LT_API = "https://www.librarything.com/services/rest/1.1/"
LT_BASE = "https://www.librarything.com"
HEADERS = {
    "User-Agent": "heritage-research/1.0 (https://github.com/aerolirian/heritage-research)"
}

# Public lists to scrape (server-rendered, no login needed)
PUBLIC_LISTS = [
    (f"{LT_BASE}/list/show/264", "Great Works of Western Literature"),
    (f"{LT_BASE}/list/show/1765", "Philosophical Fiction"),
    (f"{LT_BASE}/list/show/3472", "Classic European Novels"),
    (f"{LT_BASE}/list/show/287", "Books Every Intellectual Should Read"),
    (f"{LT_BASE}/list/show/5891", "20th Century Masterworks"),
]

# Known LibraryThing work IDs for high-priority PD works
TRACKED_WORKS = [
    ("1234", "Thomas Mann", "Buddenbrooks"),
    ("1877", "Franz Kafka", "The Trial"),
    ("5463", "Knut Hamsun", "Growth of the Soil"),
    ("1233", "James Joyce", "Ulysses"),
    ("3297", "F. Scott Fitzgerald", "The Great Gatsby"),
    ("2555", "Fyodor Dostoevsky", "Crime and Punishment"),
    ("1538", "Leo Tolstoy", "Anna Karenina"),
    ("1602", "Gustave Flaubert", "Madame Bovary"),
    ("2818", "Virginia Woolf", "Mrs Dalloway"),
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "hardy": "Thomas Hardy",
}


def scan(config):
    candidates = []
    api_key = config.get("librarything_api_key", "")

    # API lookup for tracked works
    if api_key:
        for work_id, author, title in TRACKED_WORKS:
            try:
                resp = requests.get(LT_API, params={
                    "method": "librarything.ck.getwork",
                    "id": work_id,
                    "apikey": api_key,
                    "response": "json",
                }, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                work = data.get("ltml", {}).get("item", {})
                members = work.get("members", 0)
                rating = work.get("rating", "")
                candidates.append({
                    "source": "librarything",
                    "author": author,
                    "title": title,
                    "lt_members": members,
                    "lt_rating": rating,
                    "why_now": f"LibraryThing: {members:,} members cataloged — {rating}/5",
                    "raw_score": min(50, (members or 0) / 200),
                })
            except Exception as e:
                print(f"  [librarything/api/{title}] {e}")

    # Scrape public lists (server-rendered HTML — works without API key)
    for url, list_name in PUBLIC_LISTS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")

            for i, row in enumerate(soup.select("tr.list-item, .book-row, li.listitem")[:50], 1):
                title_el = row.select_one(".title, a[href*='/work/']")
                author_el = row.select_one(".author, .authorName")
                title = title_el.get_text(strip=True) if title_el else ""
                author = author_el.get_text(strip=True) if author_el else ""

                combined = (title + " " + author).lower()
                if any(kw in combined for kw in AUTHOR_KEYWORDS):
                    matched = next(full for kw, full in AUTHOR_KEYWORDS.items() if kw in combined)
                    candidates.append({
                        "source": "librarything",
                        "author": author or matched,
                        "title": title,
                        "lt_list": list_name,
                        "lt_list_rank": i,
                        "why_now": f"LibraryThing '{list_name}' rank #{i}",
                        "raw_score": max(10, 40 - i * 0.5),
                    })
        except Exception as e:
            print(f"  [librarything/{list_name}] {e}")

    return candidates
