"""
The Marginalian (formerly Brain Pickings) scanner — Maria Popova's philosophical
essay readership. One of the most-read literary/philosophy blogs on the internet.
Marginalian readers = Heritage Canon demographic almost by definition.
Uses RSS feed — reliable, fast, no Playwright needed.
Also monitors: Brain Pickings archive feed, Popova's newsletter.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta

FEEDS = [
    ("https://www.themarginalian.org/feed/", "The Marginalian"),
    ("https://www.themarginalian.org/feed/atom/", "The Marginalian (Atom)"),
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
    "kierkegaard": "Søren Kierkegaard", "schopenhauer": "Arthur Schopenhauer",
    "weil": "Simone Weil", "arendt": "Hannah Arendt",
    "benjamin": "Walter Benjamin", "adorno": "Theodor Adorno",
    "proust": "Marcel Proust", "borges": "Jorge Luis Borges",
}


def scan(config):
    candidates = []
    cutoff = date.today() - timedelta(days=CUTOFF_DAYS)
    seen_titles = set()

    for feed_url, pub_name in FEEDS:
        try:
            resp = requests.get(feed_url, timeout=15, headers={
                "User-Agent": "heritage-research/1.0 (https://github.com/aerolirian/heritage-research)"
            })
            if resp.status_code != 200:
                continue

            # Handle both RSS and Atom
            content = resp.content
            root = ET.fromstring(content)

            # RSS items
            items = root.findall(".//item")
            # Atom entries
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            if not items:
                items = root.findall(".//atom:entry", ns)

            for item in items:
                title_el = (item.find("title") or
                            item.find("{http://www.w3.org/2005/Atom}title"))
                if title_el is None:
                    continue

                title = title_el.text or ""
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                desc_el = (item.find("description") or
                           item.find("{http://www.w3.org/2005/Atom}summary") or
                           item.find("{http://www.w3.org/2005/Atom}content"))
                link_el = (item.find("link") or
                           item.find("{http://www.w3.org/2005/Atom}link"))
                date_el = (item.find("pubDate") or
                           item.find("{http://www.w3.org/2005/Atom}updated"))

                desc = desc_el.text or "" if desc_el is not None else ""
                link = (link_el.text or link_el.get("href", "")) if link_el is not None else ""
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
                            "source": "marginalian",
                            "author": full_name,
                            "title": "",
                            "marginalian_title": title,
                            "marginalian_url": link,
                            "pub_date": pub_date_str[:16],
                            "why_now": f"The Marginalian: '{title[:70]}' — HC demographic primed",
                            "raw_score": 50,
                        })
                        break

        except Exception as e:
            print(f"  [marginalian/{pub_name}] {e}")

    return candidates
