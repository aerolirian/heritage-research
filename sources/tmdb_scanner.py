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


def _tv_is_active(tmdb_id, headers, today, window_start):
    """Return (is_active, last_air_date_str, status) for a TV show."""
    try:
        resp = requests.get(f"{TMDB_BASE}/tv/{tmdb_id}", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "")
        last_air = data.get("last_air_date", "") or ""
        next_ep = data.get("next_episode_to_air")
        # Active if: returning/in-production, OR has aired recently, OR has upcoming episode
        if status in ("Returning Series", "In Production"):
            return True, last_air, status
        if last_air:
            try:
                if date.fromisoformat(last_air) >= window_start:
                    return True, last_air, status
            except ValueError:
                pass
        if next_ep:
            return True, last_air, status
        return False, last_air, status
    except Exception:
        return False, "", ""


def scan(config):
    api_key = config.get("tmdb_api_key", "")
    if not api_key:
        print("  [tmdb] no api key — skipping")
        return []

    candidates = []
    today = date.today()
    window_start = today - timedelta(days=180)
    window_end = today + timedelta(days=365)

    headers = {"Authorization": f"Bearer {api_key}", "accept": "application/json"}

    for title in KNOWN_PD_WORKS:
        try:
            resp = requests.get(f"{TMDB_BASE}/search/multi", params={
                "query": title,
            }, headers=headers, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("results", [])

            for r in results[:3]:
                media_type = r.get("media_type", "movie")
                tmdb_id = r.get("id")
                adaptation_name = r.get("title") or r.get("name", "")

                if media_type == "tv":
                    # For TV: first_air_date only tells when the show started.
                    # Check if it's currently active (returning/in-production/recently aired).
                    active, last_air, status = _tv_is_active(tmdb_id, headers, today, window_start)
                    if not active:
                        continue
                    ref_date_str = last_air or r.get("first_air_date", "")
                    status_label = status or "TV series"
                    why = f"Active TV adaptation ({status_label})" + (
                        f" — last aired {last_air}" if last_air else ""
                    )
                else:
                    release = r.get("release_date", "")
                    if not release:
                        continue
                    try:
                        rel_date = date.fromisoformat(release)
                    except ValueError:
                        continue
                    if not (window_start <= rel_date <= window_end):
                        continue
                    ref_date_str = release
                    why = f"{'Upcoming' if rel_date >= today else 'Recent'} film adaptation releasing {release}"

                candidates.append({
                    "source": "tmdb",
                    "title": title,
                    "author": "",
                    "adaptation_title": adaptation_name,
                    "adaptation_type": media_type,
                    "release_date": ref_date_str,
                    "tmdb_id": tmdb_id,
                    "tmdb_popularity": r.get("popularity", 0),
                    "why_now": why,
                    "raw_score": 80 + min(20, r.get("popularity", 0) / 10),
                })
        except Exception as e:
            print(f"  [tmdb/{title}] {e}")

    return candidates
