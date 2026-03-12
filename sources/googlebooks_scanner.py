"""
Google Books scanner — competitor edition analysis and reader review signals.
Free API (1,000 req/day without key; 1M/day with free key from console.cloud.google.com).
Enables same-project API key as YouTube Data API.

Signals:
- What annotated/philosophical editions of PD works already exist (and how good/bad they are)
- Review counts and ratings on competitor editions
- Gaps: high-demand titles with no serious annotated edition
"""
import requests

GB_API = "https://www.googleapis.com/books/v1/volumes"

SEARCH_QUERIES = [
    "annotated philosophical edition classic literature",
    "thomas mann annotated",
    "kafka annotated introduction",
    "dostoevsky philosophical edition",
    "tolstoy annotated critical",
    "james joyce introduction critical",
    "virginia woolf annotated",
    "hemingway annotated literary",
    "fitzgerald gatsby annotated",
    "flaubert annotated critical introduction",
    "philosophical introduction classic novel",
    "heritage edition public domain literary",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov",
}


def scan(config):
    api_key = config.get("google_books_api_key", "")
    candidates = []

    for query in SEARCH_QUERIES:
        try:
            params = {
                "q": query,
                "maxResults": 20,
                "orderBy": "relevance",
                "printType": "books",
            }
            if api_key:
                params["key"] = api_key

            resp = requests.get(GB_API, params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json().get("items", [])

            for item in items:
                info = item.get("volumeInfo", {})
                title = info.get("title", "")
                authors = ", ".join(info.get("authors", []))
                rating = info.get("averageRating", 0)
                ratings_count = info.get("ratingsCount", 0)
                description = info.get("description", "")[:300]
                published = info.get("publishedDate", "")[:4]

                combined = (title + " " + authors + " " + description).lower()
                matched_author = next(
                    (full for kw, full in AUTHOR_KEYWORDS.items() if kw in combined),
                    ""
                )

                if matched_author:
                    candidates.append({
                        "source": "googlebooks",
                        "author": matched_author,
                        "title": title,
                        "competitor_authors": authors,
                        "gb_rating": rating,
                        "gb_ratings_count": ratings_count,
                        "gb_published": published,
                        "gb_description": description,
                        "search_query": query,
                        "why_now": f"Competitor edition: '{title[:60]}' by {authors} ({published}) — {ratings_count} ratings",
                        "raw_score": 20 + min(20, ratings_count / 10),
                    })

        except Exception as e:
            print(f"  [googlebooks/{query[:30]}] {e}")

    return candidates
