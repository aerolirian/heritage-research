"""
Podcast RSS scanner — which authors are getting episode-length treatment.
Literary podcasts = high-intent, deep-engagement audience.
A dedicated episode on a PD author = 30-60 min of audience immersion = primed buyer.
Uses RSS feeds directly — no auth, no scraping needed.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta

# High-signal literary/philosophical podcasts with public RSS feeds
PODCAST_FEEDS = [
    ("https://feeds.megaphone.fm/newyorkerfiction", "New Yorker Fiction Podcast"),
    ("https://feeds.transistor.fm/the-history-of-literature", "History of Literature"),
    ("https://literarydisco.libsyn.com/rss", "Literary Disco"),
    ("https://feeds.feedburner.com/bbcradio3inourtime", "In Our Time (BBC R3)"),
    ("https://feeds.npr.org/510019/podcast.xml", "NPR Books"),
    ("https://feeds.feedburner.com/newbooksnetwork", "New Books Network"),
    ("https://philosophybites.libsyn.com/rss", "Philosophy Bites"),
    ("https://partiallyexaminedlife.com/feed/podcast/", "The Partially Examined Life"),
    ("https://historyofphilosophy.net/feed", "History of Philosophy Without Gaps"),
    ("https://feeds.soundcloud.com/users/soundcloud:users:211911700/sounds.rss", "Entitled Opinions"),
]

CUTOFF_DAYS = 180

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "nietzsche": "Friedrich Nietzsche",
    "camus": "Albert Camus", "rilke": "Rainer Maria Rilke",
    "musil": "Robert Musil", "zola": "Emile Zola",
}


def scan(config):
    candidates = []
    cutoff = date.today() - timedelta(days=CUTOFF_DAYS)

    for feed_url, podcast_name in PODCAST_FEEDS:
        try:
            resp = requests.get(feed_url, timeout=15, headers={
                "User-Agent": "heritage-research/1.0 (https://github.com/aerolirian/heritage-research)"
            })
            resp.raise_for_status()

            root = ET.fromstring(resp.content)
            ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}

            for item in root.findall(".//item"):
                title_el = item.find("title")
                desc_el = item.find("description")
                date_el = item.find("pubDate")

                if title_el is None:
                    continue

                title = title_el.text or ""
                desc = desc_el.text or "" if desc_el is not None else ""
                pub_date_str = date_el.text or "" if date_el is not None else ""

                # Parse pub date (RFC 822 format)
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
                            "source": "podcast",
                            "author": full_name,
                            "title": "",
                            "podcast_name": podcast_name,
                            "podcast_episode": title,
                            "podcast_feed": feed_url,
                            "pub_date": pub_date_str[:16],
                            "why_now": f"Podcast episode: '{title[:70]}' on {podcast_name}",
                            "raw_score": 45,
                        })
                        break

        except Exception as e:
            print(f"  [podcast/{podcast_name[:30]}] {e}")

    return candidates
