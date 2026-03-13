"""
Brave Search API scanner — monitors news and op-eds referencing PD authors.
Catches authors suddenly cited in political discourse, speeches, viral essays.
"""
import requests

BRAVE_API = "https://api.search.brave.com/res/v1/web/search"

SEARCH_QUERIES = [
    "public domain classic novel annotated edition 2026",
    "Thomas Mann relevance today",
    "Kafka bureaucracy 2026",
    "Sinclair Lewis America fascism",
    "Dostoevsky modern relevance",
    "Hamsun nature isolation modern",
    "Virginia Woolf consciousness stream modern",
    "classic literature film adaptation 2025 2026",
    "Nietzsche resurgence contemporary",
    "Tolstoy war modern",
]

# X/Twitter-specific queries — covers the gap when twscrape has no active account
X_QUERIES = [
    "site:x.com Thomas Mann",
    "site:x.com Kafka book",
    "site:x.com Sinclair Lewis",
    "site:x.com Knut Hamsun",
    "site:x.com James Joyce Portrait Artist",
    "site:x.com F. Scott Fitzgerald Gatsby",
    "site:x.com classic literature philosophical",
    "site:x.com public domain annotated edition",
]


def scan(config):
    api_key = config.get("brave_api_key", "")
    if not api_key:
        print("  [brave] no api key — skipping")
        return []

    candidates = []
    seen_urls = set()

    for query in SEARCH_QUERIES + X_QUERIES:
        try:
            resp = requests.get(BRAVE_API, params={
                "q": query,
                "count": 10,
                "freshness": "pm",  # past month
            }, headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            }, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("web", {}).get("results", [])

            for r in results:
                url = r.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                title = r.get("title", "")
                desc = r.get("description", "")
                # Heuristic: extract author mentions from title/desc
                for author_last in ["Mann", "Kafka", "Lewis", "Joyce", "Woolf",
                                    "Hamsun", "Dostoevsky", "Tolstoy", "Hemingway",
                                    "Fitzgerald", "Conrad", "Chekhov", "Flaubert"]:
                    if author_last.lower() in title.lower() or author_last.lower() in desc.lower():
                        is_x = "site:x.com" in query
                        candidates.append({
                            "source": "twitter" if is_x else "brave",
                            "author": author_last,
                            "title": "",
                            "news_title": title,
                            "news_url": url,
                            "news_desc": desc[:200],
                            "search_query": query,
                            "why_now": f"Recently in news/discourse: {title[:80]}",
                            "raw_score": 30,
                        })
                        break
        except Exception as e:
            print(f"  [brave/{query[:30]}] {e}")

    return candidates
