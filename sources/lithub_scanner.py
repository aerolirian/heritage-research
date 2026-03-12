"""
Literary Hub scanner — biggest online literary publication.
Aggregates coverage from NYT, New Yorker, Guardian, Paris Review, etc.
What's trending on LitHub = what the entire serious literary readership is seeing.
Uses RSS feed (lithub.com/feed/) — reliable, no Playwright needed.
Also monitors: The Millions, Electric Literature, Los Angeles Review of Books.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta

PUBLICATION_FEEDS = [
    ("https://lithub.com/feed/", "Literary Hub"),
    ("https://themillions.com/feed", "The Millions"),
    ("https://electricliterature.com/feed/", "Electric Literature"),
    ("https://lareviewofbooks.org/feed/", "LA Review of Books"),
    ("https://theparisreview.org/feed", "The Paris Review"),
    ("https://www.thenation.com/feed/?post_type=article&subject=books-and-arts", "The Nation Books"),
    ("https://www.nybooks.com/feed/", "New York Review of Books"),
    ("https://bostonreview.net/feed/", "Boston Review"),
    ("https://thepointmag.com/feed/", "The Point Magazine"),
]

CUTOFF_DAYS = 90

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "nietzsche": "Friedrich Nietzsche",
    "camus": "Albert Camus", "rilke": "Rainer Maria Rilke",
    "zola": "Emile Zola", "faulkner": "William Faulkner",
    "steinbeck": "John Steinbeck", "hardy": "Thomas Hardy",
    "dickens": "Charles Dickens", "hugo": "Victor Hugo",
    "musil": "Robert Musil", "broch": "Hermann Broch",
    "svevo": "Italo Svevo", "pirandello": "Luigi Pirandello",
    "proust": "Marcel Proust", "gide": "André Gide",
}


def scan(config):
    candidates = []
    cutoff = date.today() - timedelta(days=CUTOFF_DAYS)

    for feed_url, pub_name in PUBLICATION_FEEDS:
        try:
            resp = requests.get(feed_url, timeout=15, headers={
                "User-Agent": "heritage-research/1.0 (https://github.com/aerolirian/heritage-research)"
            })
            if resp.status_code != 200:
                continue

            root = ET.fromstring(resp.content)

            for item in root.findall(".//item"):
                title_el = item.find("title")
                desc_el = item.find("description")
                date_el = item.find("pubDate")
                link_el = item.find("link")

                if title_el is None:
                    continue

                title = title_el.text or ""
                desc = desc_el.text or "" if desc_el is not None else ""
                link = link_el.text or "" if link_el is not None else ""
                pub_date_str = date_el.text or "" if date_el is not None else ""

                try:
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_date_str).date()
                    if pub_date < cutoff:
                        continue
                except Exception:
                    pass

                combined = (title + " " + desc[:500]).lower()
                for kw, full_name in AUTHOR_KEYWORDS.items():
                    if kw in combined:
                        candidates.append({
                            "source": "lithub",
                            "author": full_name,
                            "title": "",
                            "lithub_pub": pub_name,
                            "lithub_title": title,
                            "lithub_url": link,
                            "pub_date": pub_date_str[:16],
                            "why_now": f"{pub_name}: '{title[:70]}'",
                            "raw_score": 45,
                        })
                        break

        except Exception as e:
            print(f"  [lithub/{pub_name}] {e}")

    return candidates
