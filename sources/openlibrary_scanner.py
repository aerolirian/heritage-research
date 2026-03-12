"""
Open Library scanner — Internet Archive's book catalog.
Borrow counts and reading lists reflect actual reader demand for PD works.
Uses the free Open Library API — no auth required.
"""
import requests

OL_API = "https://openlibrary.org"
OL_SEARCH = f"{OL_API}/search.json"

SEARCH_QUERIES = [
    {"subject": "philosophical fiction", "sort": "readinglog"},
    {"subject": "classic literature", "sort": "readinglog"},
    {"subject": "modernist literature", "sort": "readinglog"},
    {"subject": "european fiction", "sort": "readinglog"},
]

# Known OL work keys for high-priority PD works
TRACKED_WORKS = [
    ("/works/OL52849W", "Fyodor Dostoevsky", "Crime and Punishment"),
    ("/works/OL98713W", "Leo Tolstoy", "Anna Karenina"),
    ("/works/OL27482W", "Franz Kafka", "The Trial"),
    ("/works/OL15534965W", "Thomas Mann", "Buddenbrooks"),
    ("/works/OL50872W", "Gustave Flaubert", "Madame Bovary"),
    ("/works/OL15301714W", "James Joyce", "Ulysses"),
    ("/works/OL36251W", "Virginia Woolf", "Mrs Dalloway"),
    ("/works/OL65532W", "F. Scott Fitzgerald", "The Great Gatsby"),
    ("/works/OL66534W", "Ernest Hemingway", "The Sun Also Rises"),
    ("/works/OL274116W", "Knut Hamsun", "Growth of the Soil"),
]


def scan(config):
    candidates = []

    # Check borrow/reading stats for tracked works
    for work_key, author, title in TRACKED_WORKS:
        try:
            resp = requests.get(f"{OL_API}{work_key}.json", timeout=10, headers={
                "User-Agent": "heritage-research/1.0 (https://github.com/aerolirian/heritage-research)"
            })
            if resp.status_code != 200:
                continue
            data = resp.json()

            # Get reading log count
            stats_resp = requests.get(
                f"{OL_API}{work_key}/bookshelves.json", timeout=10,
                headers={"User-Agent": "heritage-research/1.0"}
            )
            stats = stats_resp.json() if stats_resp.status_code == 200 else {}
            want_to_read = stats.get("counts", {}).get("want_to_read", 0)
            currently_reading = stats.get("counts", {}).get("currently_reading", 0)
            already_read = stats.get("counts", {}).get("already_read", 0)

            total = want_to_read + currently_reading + already_read
            if total > 100:
                candidates.append({
                    "source": "openlibrary",
                    "author": author,
                    "title": title,
                    "ol_want_to_read": want_to_read,
                    "ol_currently_reading": currently_reading,
                    "ol_already_read": already_read,
                    "ol_total": total,
                    "why_now": f"Open Library: {want_to_read:,} want to read, {currently_reading:,} currently reading",
                    "raw_score": min(60, total / 500),
                })
        except Exception as e:
            print(f"  [openlibrary/{title}] {e}")

    # Search for high-readinglog works by subject
    for params in SEARCH_QUERIES:
        try:
            resp = requests.get(OL_SEARCH, params={
                **params,
                "fields": "title,author_name,first_publish_year,readinglog_count",
                "limit": 20,
            }, timeout=15, headers={
                "User-Agent": "heritage-research/1.0"
            })
            resp.raise_for_status()
            docs = resp.json().get("docs", [])

            for doc in docs:
                year = doc.get("first_publish_year", 9999)
                if year > 1954:  # outside life+70 PD window
                    continue
                candidates.append({
                    "source": "openlibrary",
                    "author": ", ".join(doc.get("author_name", [])[:1]),
                    "title": doc.get("title", ""),
                    "ol_readinglog": doc.get("readinglog_count", 0),
                    "first_publish_year": year,
                    "why_now": f"Open Library reading demand: {doc.get('readinglog_count', 0):,} in reading lists",
                    "raw_score": min(50, (doc.get("readinglog_count", 0) or 0) / 1000),
                })
        except Exception as e:
            print(f"  [openlibrary/search] {e}")

    return candidates
