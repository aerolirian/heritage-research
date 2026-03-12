"""
Hacker News scanner — uses Algolia HN API (no auth required).
Targets the Heritage Canon demographic: technical/intellectual readers.
"""
import requests
from collections import defaultdict

HN_API = "https://hn.algolia.com/api/v1/search"

TRACKED_AUTHORS = [
    "Thomas Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy",
    "Hamsun", "Sinclair Lewis", "Virginia Woolf", "Conrad",
    "Hemingway", "Faulkner", "Chekhov", "Flaubert", "Zola",
]


def scan(config):
    candidates = []
    mention_counts = defaultdict(lambda: {"count": 0, "hits": []})

    for author in TRACKED_AUTHORS:
        try:
            resp = requests.get(HN_API, params={
                "query": author,
                "tags": "story",
                "hitsPerPage": 20,
            }, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", [])
            if hits:
                mention_counts[author]["count"] += len(hits)
                for hit in hits[:3]:
                    mention_counts[author]["hits"].append({
                        "title": hit.get("title", ""),
                        "url": hit.get("url", ""),
                        "points": hit.get("points", 0),
                    })
        except Exception as e:
            print(f"  [hn/{author}] {e}")

    for author, data in mention_counts.items():
        if data["count"] >= 1:
            candidates.append({
                "source": "hn",
                "author": author,
                "title": "",
                "why_now": f"Discussed on Hacker News ({data['count']} recent threads)",
                "sample_posts": data["hits"],
                "raw_score": data["count"],
            })

    return candidates
