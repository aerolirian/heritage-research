"""
Substack scanner — literary newsletters and their reader engagement.
Uses RSS feeds (each publication exposes /feed) — fast, reliable, no Playwright needed.
Falls back to Playwright search for discovery across all Substacks.

High-signal target publications (all have public RSS feeds):
- The Honest Broker (Ted Gioia) — 300k+ subs, books/music/culture
- The Intrinsic Perspective (Erik Hoel) — philosophy of mind + literature
- Astral Codex Ten (Scott Alexander) — rationalist/philosophy, huge readership
- Freddie deBoer — literary criticism, education
- Sam Kriss — philosophical essays, cultural criticism
- The Paris Review Notes — official Paris Review substack
- The Critic — serious literary/cultural criticism
- The Point Magazine — philosophy and culture
"""
import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta

PUBLICATION_FEEDS = [
    ("https://tedgioia.substack.com/feed", "The Honest Broker"),
    ("https://erikhoel.substack.com/feed", "The Intrinsic Perspective"),
    ("https://astralcodexten.substack.com/feed", "Astral Codex Ten"),
    ("https://freddiedeboer.substack.com/feed", "Freddie deBoer"),
    ("https://samkriss.substack.com/feed", "Sam Kriss"),
    ("https://theparisreview.substack.com/feed", "The Paris Review Notes"),
    ("https://thecritic.substack.com/feed", "The Critic"),
    ("https://thepointmag.substack.com/feed", "The Point Magazine"),
    ("https://josephheath.substack.com/feed", "In Due Course"),
    ("https://alexdanco.substack.com/feed", "Alex Danco"),
    ("https://edwest.substack.com/feed", "Ed West"),
    ("https://unherd.substack.com/feed", "UnHerd"),
    ("https://lithub.substack.com/feed", "Literary Hub"),
    ("https://electricliterature.substack.com/feed", "Electric Literature"),
    ("https://themillions.substack.com/feed", "The Millions"),
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
    "zola": "Emile Zola", "faulkner": "William Faulkner",
    "steinbeck": "John Steinbeck", "dreiser": "Theodore Dreiser",
    "hardy": "Thomas Hardy", "dickens": "Charles Dickens",
    "hugo": "Victor Hugo", "balzac": "Honoré de Balzac",
}


def scan(config):
    candidates = []
    cutoff = date.today() - timedelta(days=CUTOFF_DAYS)

    for feed_url, pub_name in PUBLICATION_FEEDS:
        try:
            resp = requests.get(feed_url, timeout=10, headers={
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

                combined = (title + " " + desc[:800]).lower()
                for kw, full_name in AUTHOR_KEYWORDS.items():
                    if kw in combined:
                        candidates.append({
                            "source": "substack",
                            "author": full_name,
                            "title": "",
                            "substack_pub": pub_name,
                            "substack_title": title,
                            "substack_url": link,
                            "pub_date": pub_date_str[:16],
                            "why_now": f"Substack essay: '{title[:70]}' ({pub_name})",
                            "raw_score": 40,
                        })
                        break

        except Exception as e:
            print(f"  [substack/{pub_name}] {e}")

    return candidates
