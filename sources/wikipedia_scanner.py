"""
Wikipedia pageview scanner — author/title page traffic spikes indicate cultural moment.
Uses the free Wikimedia Pageviews API (no auth required).
A spike = someone famous mentioned the author, a film was announced, political discourse.
"""
import requests
from datetime import date, timedelta

PAGEVIEWS_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article}/daily/{start}/{end}"

TRACKED_ARTICLES = [
    # Author pages
    ("Thomas_Mann", "Thomas Mann", ""),
    ("Franz_Kafka", "Franz Kafka", ""),
    ("James_Joyce", "James Joyce", ""),
    ("Knut_Hamsun", "Knut Hamsun", ""),
    ("Sinclair_Lewis", "Sinclair Lewis", ""),
    ("Virginia_Woolf", "Virginia Woolf", ""),
    ("F._Scott_Fitzgerald", "F. Scott Fitzgerald", ""),
    ("Fyodor_Dostoevsky", "Fyodor Dostoevsky", ""),
    ("Leo_Tolstoy", "Leo Tolstoy", ""),
    ("Ernest_Hemingway", "Ernest Hemingway", ""),
    ("Joseph_Conrad", "Joseph Conrad", ""),
    ("Gustave_Flaubert", "Gustave Flaubert", ""),
    ("Anton_Chekhov", "Anton Chekhov", ""),
    ("Emile_Zola", "Emile Zola", ""),
    ("Victor_Hugo", "Victor Hugo", ""),
    ("Thomas_Hardy", "Thomas Hardy", ""),
    # Title pages for high-value works
    ("The_Trial_(novel)", "Franz Kafka", "The Trial"),
    ("Buddenbrooks", "Thomas Mann", "Buddenbrooks"),
    ("Growth_of_the_Soil", "Knut Hamsun", "Growth of the Soil"),
    ("Ulysses_(novel)", "James Joyce", "Ulysses"),
    ("The_Great_Gatsby", "F. Scott Fitzgerald", "The Great Gatsby"),
    ("Crime_and_Punishment", "Fyodor Dostoevsky", "Crime and Punishment"),
    ("Anna_Karenina", "Leo Tolstoy", "Anna Karenina"),
    ("Madame_Bovary", "Gustave Flaubert", "Madame Bovary"),
    ("Wuthering_Heights", "Emily Brontë", "Wuthering Heights"),
    ("The_Picture_of_Dorian_Gray", "Oscar Wilde", "The Picture of Dorian Gray"),
]

SPIKE_THRESHOLD = 1.5  # 50% above 90-day average = signal


def scan(config):
    candidates = []
    today = date.today()
    end = today - timedelta(days=1)
    start_90 = today - timedelta(days=90)
    start_recent = today - timedelta(days=14)

    fmt = "%Y%m%d"

    for article, author, title in TRACKED_ARTICLES:
        try:
            url = PAGEVIEWS_API.format(
                article=article,
                start=start_90.strftime(fmt),
                end=end.strftime(fmt),
            )
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "heritage-research/1.0 (https://github.com/aerolirian/heritage-research)"
            })
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if len(items) < 14:
                continue

            views = [x["views"] for x in items]
            avg_90 = sum(views) / len(views)
            recent = sum(views[-14:]) / 14  # last 2 weeks

            if avg_90 > 0 and recent / avg_90 >= SPIKE_THRESHOLD:
                ratio = round(recent / avg_90, 2)
                candidates.append({
                    "source": "wikipedia",
                    "author": author,
                    "title": title or "",
                    "wiki_article": article,
                    "wiki_avg_daily": round(avg_90),
                    "wiki_recent_daily": round(recent),
                    "wiki_spike_ratio": ratio,
                    "why_now": f"Wikipedia traffic spike {ratio}x above 90-day avg ({round(recent):,} views/day)",
                    "raw_score": min(100, ratio * 30),
                })
        except Exception as e:
            print(f"  [wikipedia/{article}] {e}")

    return candidates
