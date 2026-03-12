"""
Project Gutenberg download rankings — top 100 most-downloaded books.
Books in top 100 without a good annotated edition = direct demand signal.
"""
import requests
from bs4 import BeautifulSoup

GUTENBERG_TOP_URL = "https://www.gutenberg.org/browse/scores/top"


def scan(config):
    candidates = []
    try:
        resp = requests.get(GUTENBERG_TOP_URL, timeout=15, headers={
            "User-Agent": "heritage-research/1.0 (+https://github.com/aerolirian/heritage-research)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Top books listed as ordered list items
        for rank, li in enumerate(soup.select("ol li a"), 1):
            if rank > 100:
                break
            title = li.get_text(strip=True)
            href = li.get("href", "")
            gutenberg_id = href.split("/")[-1] if href else ""
            candidates.append({
                "source": "gutenberg",
                "title": title,
                "author": "",  # parsed separately from title string
                "gutenberg_id": gutenberg_id,
                "gutenberg_rank": rank,
                "why_now": f"Gutenberg rank #{rank} — high sustained download demand",
                "raw_score": max(0, 100 - rank),
            })
    except Exception as e:
        print(f"  [gutenberg] {e}")

    return candidates
