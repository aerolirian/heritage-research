#!/usr/bin/env python3
"""
promote.py — Zero/low-cost promotion engine for Heritage Canon books.

Consumes the weekly research sweep output + published catalog to generate:
- Timed promotion alerts (Wikipedia spikes, film windows, anniversaries)
- Outreach email drafts to Five Books experts, Substack writers, podcast hosts, YouTube creators
- Reddit comment drafts for organic participation
- Substack/social post drafts exploiting cultural moments
- Archive.org / Zenodo article submission

Usage:
    python promote.py                        # full weekly promotion run
    python promote.py --book arrowsmith      # single book
    python promote.py --mode alerts          # only print time-sensitive alerts
    python promote.py --mode outreach        # only generate outreach drafts
    python promote.py --mode content         # only generate social/post content
    python promote.py --mode submit          # submit articles to Archive.org + Zenodo
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import date, timedelta

from openai import OpenAI

CONFIG_PATH = Path.home() / ".heritage_research.json"
CATALOG_PATH = Path("catalog.json")
OUTPUT_DIR = Path("promotion_output")

# Heritage Canon published catalog
# Populate this with your published books
DEFAULT_CATALOG = [
    {"slug": "arrowsmith",            "title": "Arrowsmith", "full_title": "Arrowsmith: Philosophical Edition — The Cost of Scientific Obsession", "author": "Sinclair Lewis",        "genre": "Novel", "google_play_url": "", "apple_url": "", "kobo_url": ""},
    {"slug": "the_great_gatsby",      "title": "The Great Gatsby", "full_title": "The Great Gatsby: Philosophical Edition — The Lie at the Heart of the American Dream", "author": "F. Scott Fitzgerald", "genre": "Novel", "google_play_url": "", "apple_url": "", "kobo_url": ""},
    {"slug": "buddenbrooks",          "title": "Buddenbrooks", "full_title": "Buddenbrooks: Philosophical Edition — Decadence and the Logic of Historical Form", "author": "Thomas Mann",          "genre": "Novel", "google_play_url": "", "apple_url": "", "kobo_url": ""},
    {"slug": "growth_of_the_soil",    "title": "Growth of the Soil", "full_title": "Growth of the Soil: Philosophical Edition — The Case Against Civilisation", "author": "Knut Hamsun",          "genre": "Novel", "google_play_url": "", "apple_url": "", "kobo_url": ""},
    {"slug": "a_portrait_of_the_artist", "title": "A Portrait of the Artist as a Young Man", "full_title": "A Portrait of the Artist as a Young Man: Philosophical Edition — The Price of Self-Creation", "author": "James Joyce", "genre": "Novel", "google_play_url": "", "apple_url": "", "kobo_url": ""},
]


def load_config():
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}")
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def load_catalog():
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text())
    return DEFAULT_CATALOG


def load_candidates():
    path = Path("output/candidates.json")
    if not path.exists():
        print("No candidates.json — run: python research.py sweep")
        return []
    return json.loads(path.read_text())


def load_report():
    path = Path("output/report.md")
    if path.exists():
        return path.read_text()
    return ""


def cmd_full(args, config, catalog, candidates):
    OUTPUT_DIR.mkdir(exist_ok=True)
    book_filter = args.book if hasattr(args, "book") else None
    books = [b for b in catalog if not book_filter or b["slug"] == book_filter]

    alerts = generate_alerts(candidates, books)
    outreach = generate_outreach(candidates, books, config)
    content = generate_content(candidates, books, config)

    # Write outputs
    summary_lines = [f"# Heritage Canon Promotion — {date.today()}\n"]

    if alerts:
        summary_lines.append("## TIME-SENSITIVE ALERTS\n")
        for a in alerts:
            summary_lines.append(f"### {a['type']} — {a['book'] or a.get('author', '')}")
            summary_lines.append(f"**Action**: {a['action']}")
            summary_lines.append(f"**Window**: {a['window']}\n")
            summary_lines.append(a.get("draft", "") + "\n---\n")

    if outreach:
        summary_lines.append("## OUTREACH DRAFTS\n")
        for o in outreach:
            summary_lines.append(f"### {o['type']} → {o['target']}")
            summary_lines.append(f"**Subject**: {o['subject']}\n")
            summary_lines.append(o["body"] + "\n---\n")

    if content:
        summary_lines.append("## CONTENT DRAFTS\n")
        for c in content:
            summary_lines.append(f"### {c['platform']} — {c['book']}")
            summary_lines.append(c["draft"] + "\n---\n")

    out_path = OUTPUT_DIR / f"promotion_{date.today()}.md"
    out_path.write_text("\n".join(summary_lines))
    print(f"Wrote {len(alerts)} alerts, {len(outreach)} outreach drafts, {len(content)} content drafts")
    print(f"→ {out_path}")


# ---------------------------------------------------------------------------
# ALERTS
# ---------------------------------------------------------------------------

def generate_alerts(candidates, catalog):
    """Flag time-sensitive promotion windows for already-published books."""
    alerts = []
    published_authors = {b["author"].split()[-1].lower(): b for b in catalog}
    published_titles = {b["title"].lower(): b for b in catalog}

    for c in candidates:
        author_parts = c.get("author", "").split()
        author_last = author_parts[-1].lower() if author_parts else ""
        title_lower = c.get("title", "").lower()
        book = published_authors.get(author_last) or published_titles.get(title_lower)
        if not book:
            continue

        source = c.get("source", "")
        why = c.get("why_now", "")

        if source == "wikipedia" and c.get("wiki_spike_ratio", 1) >= 1.5:
            alerts.append({
                "type": "WIKIPEDIA SPIKE",
                "book": book["title"],
                "author": book["author"],
                "action": f"Post on Reddit + email your list today. {book['author']} Wikipedia traffic is {c['wiki_spike_ratio']}x above average.",
                "window": "48 hours",
                "draft": _draft_spike_reddit_comment(book, c),
            })

        elif source == "tmdb":
            rel = c.get("release_date", "")
            try:
                rel_date = date.fromisoformat(rel)
                days_away = (rel_date - date.today()).days
                if -14 <= days_away <= 90:
                    alerts.append({
                        "type": "FILM ADAPTATION WINDOW",
                        "book": book["title"],
                        "author": book["author"],
                        "action": f"Film '{c.get('adaptation_title','')}' releases {rel}. Push edition on Letterboxd, r/movies, r/books, r/TrueFilm.",
                        "window": f"{days_away} days" if days_away > 0 else "NOW (film already out)",
                        "draft": _draft_film_reddit_comment(book, c),
                    })
            except Exception:
                pass

        elif source == "anniversary" and abs(c.get("years_away", 99)) <= 1:
            alerts.append({
                "type": "CENTENNIAL",
                "book": book["title"],
                "author": book["author"],
                "action": f"Publication centennial {c.get('centennial_year')}. Pitch to Literary Hub, Marginalian, email list, Reddit.",
                "window": "This year",
                "draft": _draft_anniversary_post(book, c),
            })

        elif source == "reddit" and c.get("raw_score", 0) >= 5:
            alerts.append({
                "type": "REDDIT MOMENTUM",
                "book": book["title"],
                "author": book["author"],
                "action": f"Active discussion in {', '.join(c.get('subreddits', [])[:3])}. Join the conversation now.",
                "window": "Today",
                "draft": _draft_reddit_organic(book, c),
            })

    return alerts


def _draft_spike_reddit_comment(book, signal):
    return f"""**Suggested Reddit comment for r/books / r/literature:**

---
Interesting timing — I've been thinking about {book['author']} a lot lately too.
There's a philosophical edition of *{book['title']}* (Heritage Canon) that includes a 5,000-word
introduction analysing exactly [the theme from why_now]. Might be relevant if you're going deeper.
[Link to your edition]
---
*(Edit to match the specific thread context before posting)*"""


def _draft_film_reddit_comment(book, signal):
    adaptation = signal.get("adaptation_title", "the new film")
    return f"""**Suggested post for r/TrueFilm / r/movies / r/books when {adaptation} releases:**

---
If the film got you interested in the source material — the Heritage Canon edition of
*{book['title']}* has a philosophical introduction that covers exactly what most adaptations miss.
[{book['full_title']}]({book.get('google_play_url') or book.get('kobo_url') or '#'})
---"""


def _draft_anniversary_post(book, signal):
    year = signal.get("centennial_year", "")
    return f"""**Suggested Substack/newsletter post hook:**

---
{year} marks 100 years since *{book['title']}* was first published.

What {book['author']} understood that we've spent a century trying to forget...

[Heritage Canon philosophical edition — link]
---"""


def _draft_reddit_organic(book, signal):
    subs = signal.get("subreddits", [])
    return f"""**Organic participation opportunity in: {', '.join(subs)}**

Find threads discussing {book['author']} → respond genuinely to the philosophical angle →
mention the edition naturally if relevant. Don't open with a link.

Key angle from research: {signal.get('why_now', '')}"""


# ---------------------------------------------------------------------------
# OUTREACH
# ---------------------------------------------------------------------------

def generate_outreach(candidates, catalog, config):
    """Draft emails to amplifiers who just covered your published authors."""
    client = OpenAI(api_key=config.get("openai_api_key", ""))
    outreach = []
    published_authors = {b["author"].split()[-1].lower(): b for b in catalog}

    amplifier_sources = ["substack", "podcast", "lithub", "marginalian", "youtube", "fivebooks"]

    seen = set()
    for c in candidates:
        source = c.get("source", "")
        if source not in amplifier_sources:
            continue

        author_parts = c.get("author", "").split()
        author_last = author_parts[-1].lower() if author_parts else ""
        book = published_authors.get(author_last)
        if not book:
            continue

        target = (c.get("substack_pub") or c.get("podcast_name") or
                  c.get("lithub_pub") or c.get("yt_channel") or
                  c.get("fivebooks_expert") or source)
        key = f"{source}:{target}:{book['slug']}"
        if key in seen:
            continue
        seen.add(key)

        reference = (c.get("substack_title") or c.get("podcast_episode") or
                     c.get("lithub_title") or c.get("yt_title") or "your recent piece")

        subject, body = _draft_outreach_email(client, book, target, reference, source)
        outreach.append({
            "type": source,
            "target": target,
            "book": book["title"],
            "subject": subject,
            "body": body,
        })

    return outreach


def _draft_outreach_email(client, book, target, reference, source):
    prompt = f"""Draft a short, genuine outreach email (under 150 words) from the Heritage Canon
publishing team to {target}, who recently published/covered: "{reference}".

We've just published: {book['full_title']} by {book['author']}.
It includes an original 5,000-word philosophical introduction by Daniel Shilansky.

The email should:
- Reference their specific recent piece naturally (not generically)
- Offer a free review copy
- Not be sycophantic or pushy
- Sound like it's from a small independent publisher, not a PR firm
- End with a single clear ask

Return as JSON: {{"subject": "...", "body": "..."}}"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        data = json.loads(resp.choices[0].message.content)
        return data["subject"], data["body"]
    except Exception:
        return (
            f"Review copy — {book['full_title']}",
            f"Hi,\n\nI came across your recent piece on {book['author']} and thought you might be interested in our new philosophical edition: {book['full_title']}.\n\nIt includes an original 5,000-word introduction by Daniel Shilansky. Happy to send a review copy if you're interested.\n\nBest,\nHeritage Canon"
        )


# ---------------------------------------------------------------------------
# CONTENT DRAFTS
# ---------------------------------------------------------------------------

def generate_content(candidates, catalog, config):
    """Generate social/newsletter post drafts exploiting cultural moments."""
    client = OpenAI(api_key=config.get("openai_api_key", ""))
    content = []
    published_authors = {b["author"].split()[-1].lower(): b for b in catalog}

    high_signal = [c for c in candidates if c.get("score", 0) > 30][:10]

    for c in high_signal:
        author_parts = c.get("author", "").split()
        author_last = author_parts[-1].lower() if author_parts else ""
        book = published_authors.get(author_last)
        if not book:
            continue

        why_now = c.get("why_now", "")
        signals = c.get("signals", [why_now])

        draft = _draft_content_post(client, book, signals)
        content.append({
            "platform": "Substack/newsletter",
            "book": book["title"],
            "why_now": why_now,
            "draft": draft,
        })

    return content


def _draft_content_post(client, book, signals):
    prompt = f"""Write a short Substack post hook (opening paragraph only, ~80 words)
that promotes {book['full_title']} by {book['author']}.

Current cultural signals making this book urgent:
{chr(10).join(f'- {s}' for s in signals[:4])}

The post should:
- Open with the cultural moment, not the book
- Make the reader feel the urgency of reading this NOW
- End with a single sentence pointing to the Heritage Canon edition
- Sound like a thoughtful independent publisher, not a marketer"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.75,
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[Content draft failed: {e}]"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Heritage Canon promotion engine")
    parser.add_argument("--book", help="Single book slug")
    parser.add_argument("--mode", choices=["alerts", "outreach", "content", "submit"],
                        help="Run only this mode (default: all)")
    args = parser.parse_args()

    config = load_config()
    catalog = load_catalog()
    candidates = load_candidates()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.mode == "alerts":
        alerts = generate_alerts(candidates, catalog)
        for a in alerts:
            print(f"\n[{a['type']}] {a['book']} — {a['action']}")
            print(f"Window: {a['window']}")
            print(a.get("draft", ""))
    elif args.mode == "outreach":
        outreach = generate_outreach(candidates, catalog, config)
        for o in outreach:
            print(f"\n[{o['type']}] → {o['target']}")
            print(f"Subject: {o['subject']}")
            print(o["body"])
    elif args.mode == "content":
        content = generate_content(candidates, catalog, config)
        for c in content:
            print(f"\n[{c['platform']}] {c['book']}")
            print(c["draft"])
    else:
        cmd_full(args, config, catalog, candidates)


if __name__ == "__main__":
    main()
