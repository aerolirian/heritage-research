"""
Stack Exchange Literature scanner — close reading questions signal deep engagement.
Uses the free Stack Exchange API (no auth for read-only, 300 req/day without key).
High-score questions about a PD author = readers actively studying the work.
Also covers Philosophy SE for philosophical angle discovery.
"""
import requests

SE_API = "https://api.stackexchange.com/2.3"

SITES = ["literature", "philosophy"]

SEARCH_TAGS = [
    "thomas-mann", "franz-kafka", "james-joyce", "fyodor-dostoevsky",
    "leo-tolstoy", "virginia-woolf", "ernest-hemingway", "f-scott-fitzgerald",
    "gustave-flaubert", "joseph-conrad", "knut-hamsun", "anton-chekhov",
    "nietzsche", "existentialism", "modernism", "literary-criticism",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "flaubert": "Gustave Flaubert", "chekhov": "Anton Chekhov",
    "nietzsche": "Friedrich Nietzsche", "camus": "Albert Camus",
}


def scan(config):
    candidates = []
    api_key = config.get("stackexchange_api_key", "")  # optional, increases quota

    for site in SITES:
        # Get top questions by tag
        for tag in SEARCH_TAGS[:12]:
            try:
                params = {
                    "site": site,
                    "tagged": tag,
                    "sort": "votes",
                    "order": "desc",
                    "pagesize": 10,
                    "filter": "default",
                }
                if api_key:
                    params["key"] = api_key

                resp = requests.get(f"{SE_API}/questions", params=params, timeout=10)
                resp.raise_for_status()
                items = resp.json().get("items", [])

                for item in items:
                    score = item.get("score", 0)
                    if score < 3:
                        continue
                    q_title = item.get("title", "")
                    author = _extract_author(tag + " " + q_title)
                    candidates.append({
                        "source": "stackexchange",
                        "author": author,
                        "title": "",
                        "se_site": site,
                        "se_tag": tag,
                        "se_question": q_title,
                        "se_score": score,
                        "se_answers": item.get("answer_count", 0),
                        "se_url": item.get("link", ""),
                        "why_now": f"Stack Exchange {site}: '{q_title[:70]}' ({score} votes)",
                        "raw_score": min(40, 15 + score),
                    })
            except Exception as e:
                print(f"  [stackexchange/{site}/{tag}] {e}")

    return candidates


def _extract_author(text):
    t = text.lower()
    for kw, full in AUTHOR_KEYWORDS.items():
        if kw in t:
            return full
    return ""
