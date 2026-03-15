"""
TMDB scanner — finds upcoming film/TV adaptations of PD literary works.
Adaptations are the strongest urgency signal: timely, media-covered, new audience.
The intro can directly engage with (and critique) the adaptation.
"""
import requests
from datetime import date, timedelta

TMDB_BASE = "https://api.themoviedb.org/3"

# Books/authors known to have upcoming or recent adaptations
# Updated by scan() dynamically; seeded with known candidates
KNOWN_PD_WORKS = [
    "Wuthering Heights", "The Odyssey", "War and Peace", "Anna Karenina",
    "Crime and Punishment", "Madame Bovary", "The Count of Monte Cristo",
    "Les Misérables", "The Jungle Book", "Doctor Jekyll",
    "The Picture of Dorian Gray", "Dracula", "Frankenstein",
    "The Great Gatsby", "The Sun Also Rises", "A Farewell to Arms",
    "The Sound and the Fury", "As I Lay Dying", "Death in Venice",
    # High-adaptation legacy titles (previously missing)
    "1984", "Nineteen Eighty-Four", "Romeo and Juliet",
    "Lady Chatterley's Lover", "A Christmas Carol",
    "Thus Spoke Zarathustra", "Meditations",
]


def scan(config):
    api_key = config.get("tmdb_api_key", "")
    if not api_key:
        print("  [tmdb] no api key — skipping")
        return []

    candidates = []
    today = date.today()
    window_end = today + timedelta(days=365)

    headers = {"Authorization": f"Bearer {api_key}", "accept": "application/json"}

    for title in KNOWN_PD_WORKS:
        try:
            # Search for upcoming movie/TV
            resp = requests.get(f"{TMDB_BASE}/search/multi", params={
                "query": title,
            }, headers=headers, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("results", [])

            for r in results[:3]:
                release = r.get("release_date") or r.get("first_air_date", "")
                if not release:
                    continue
                try:
                    rel_date = date.fromisoformat(release)
                except ValueError:
                    continue
                if today - timedelta(days=180) <= rel_date <= window_end:
                    media_type = r.get("media_type", "movie")
                    candidates.append({
                        "source": "tmdb",
                        "title": title,
                        "author": "",
                        "adaptation_title": r.get("title") or r.get("name", ""),
                        "adaptation_type": media_type,
                        "release_date": release,
                        "tmdb_id": r.get("id"),
                        "tmdb_popularity": r.get("popularity", 0),
                        "why_now": f"{'Upcoming' if rel_date >= today else 'Recent'} {media_type} adaptation releasing {release}",
                        "raw_score": 80 + min(20, r.get("popularity", 0) / 10),
                    })
        except Exception as e:
            print(f"  [tmdb/{title}] {e}")

    return candidates
