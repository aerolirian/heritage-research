#!/usr/bin/env python3
"""
post_x.py — Review and post Heritage Canon content to X (@heritagecanon).

Uses the official X API v2 via tweepy. Requires OAuth 1.0a credentials in
~/.heritage_research.json:
    x_api_key, x_api_secret, x_access_token, x_access_token_secret

These come from developer.x.com → your app → Keys and Tokens.
The access token must be generated for the @heritagecanon account.

Usage:
    python post_x.py                     # interactive: show each draft, y/n to post
    python post_x.py --dry               # print drafts only, no posting
    python post_x.py --book arrowsmith   # only drafts for this book
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

import tweepy

CONFIG_PATH = Path.home() / ".heritage_research.json"
CATALOG_PATH = Path("catalog.json")
OUTPUT_DIR = Path("promotion_output")

DEFAULT_CATALOG = [
    {"slug": "arrowsmith",            "title": "Arrowsmith",                        "author": "Sinclair Lewis"},
    {"slug": "the_great_gatsby",      "title": "The Great Gatsby",                  "author": "F. Scott Fitzgerald"},
    {"slug": "buddenbrooks",          "title": "Buddenbrooks",                      "author": "Thomas Mann"},
    {"slug": "growth_of_the_soil",    "title": "Growth of the Soil",                "author": "Knut Hamsun"},
    {"slug": "a_portrait_of_the_artist", "title": "A Portrait of the Artist as a Young Man", "author": "James Joyce"},
]


def load_config():
    if not CONFIG_PATH.exists():
        sys.exit(f"Config not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())


def load_catalog():
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text())
    return DEFAULT_CATALOG


def get_client(config):
    for key in ("x_api_key", "x_api_secret", "x_access_token", "x_access_token_secret"):
        if not config.get(key):
            sys.exit(f"Missing {key} in config. Get credentials at developer.x.com.")
    return tweepy.Client(
        consumer_key=config["x_api_key"],
        consumer_secret=config["x_api_secret"],
        access_token=config.get("x_heritagecanon_access_token") or config["x_access_token"],
        access_token_secret=config.get("x_heritagecanon_access_token_secret") or config["x_access_token_secret"],
    )


def load_drafts(book_filter=None):
    """Load the most recent promotion output file."""
    files = sorted(OUTPUT_DIR.glob("promotion_*.md"), reverse=True)
    if not files:
        sys.exit("No promotion output found. Run: python promote.py")

    latest = files[0]
    print(f"Loading drafts from: {latest.name}\n")
    return latest.read_text()


def extract_x_drafts(promotion_text, catalog, book_filter=None):
    """
    Pull X-postable excerpts from promotion output.
    Returns list of {book, slug, text, source_type}.
    """
    drafts = []
    catalog_by_title = {b["title"].lower(): b for b in catalog}

    # Walk sections, pull content blocks
    sections = promotion_text.split("\n---\n")
    for section in sections:
        lines = section.strip().splitlines()
        if not lines:
            continue

        # Find book context from section header
        book = None
        for line in lines:
            for title_lower, b in catalog_by_title.items():
                if title_lower in line.lower():
                    book = b
                    break
            if book:
                break

        if not book:
            continue
        if book_filter and book["slug"] != book_filter:
            continue

        # Pull Substack/newsletter hooks — these are short enough to adapt for X
        in_hook = False
        hook_lines = []
        for line in lines:
            if line.startswith("---") and hook_lines:
                break
            if in_hook:
                hook_lines.append(line)
            if "suggested substack" in line.lower() or (
                "substack/newsletter" in line.lower() and "###" in line
            ):
                in_hook = True

        if hook_lines:
            text = " ".join(l.strip() for l in hook_lines if l.strip())
            if len(text) > 20:
                # Trim to 280 chars, keep it clean
                x_text = text[:260].rsplit(" ", 1)[0] + "…" if len(text) > 260 else text
                drafts.append({
                    "book": book["title"],
                    "slug": book["slug"],
                    "author": book["author"],
                    "text": x_text,
                    "source_type": "newsletter_hook",
                })

    return drafts


def generate_simple_drafts(catalog, book_filter=None):
    """
    Generate minimal X drafts when no promotion output exists.
    Used as fallback — one evergreen thread-starter per book.
    """
    drafts = []
    books = [b for b in catalog if not book_filter or b["slug"] == book_filter]
    for b in books:
        url = b.get("google_play_url") or b.get("kobo_url") or b.get("apple_url") or ""
        link = f" {url}" if url else ""
        text = (
            f"What {b['author']} understood that most readers miss — "
            f"the Heritage Canon philosophical edition of {b['title']} "
            f"has a 5,000-word introduction unpacking it.{link}"
        )
        if len(text) > 280:
            text = text[:277] + "…"
        drafts.append({
            "book": b["title"],
            "slug": b["slug"],
            "author": b["author"],
            "text": text,
            "source_type": "evergreen",
        })
    return drafts


def interactive_post(drafts, client, dry_run=False):
    if not drafts:
        print("No X drafts found.")
        return

    posted = 0
    skipped = 0

    for i, d in enumerate(drafts, 1):
        print(f"\n{'='*60}")
        print(f"Draft {i}/{len(drafts)} — {d['book']} ({d['source_type']})")
        print(f"{'='*60}")
        print(d["text"])
        print(f"\n[{len(d['text'])}/280 chars]")

        if dry_run:
            print("  [dry-run] would post ↑")
            continue

        choice = input("\nPost this? [y/n/e(dit)/q(uit)]: ").strip().lower()

        if choice == "q":
            break
        elif choice == "n":
            skipped += 1
            print("  Skipped.")
        elif choice == "e":
            print("Enter new text (blank line to finish):")
            new_lines = []
            while True:
                line = input()
                if not line:
                    break
                new_lines.append(line)
            d["text"] = " ".join(new_lines)
            print(f"\nRevised ({len(d['text'])}/280 chars):")
            print(d["text"])
            confirm = input("Post revised version? [y/n]: ").strip().lower()
            if confirm == "y":
                _post(client, d)
                posted += 1
            else:
                skipped += 1
        elif choice == "y":
            _post(client, d)
            posted += 1

    print(f"\nDone. Posted: {posted}, Skipped: {skipped}")


def _post(client, draft):
    try:
        resp = client.create_tweet(text=draft["text"])
        tweet_id = resp.data["id"]
        print(f"  Posted: https://x.com/heritagecanon/status/{tweet_id}")
    except tweepy.TweepyException as e:
        print(f"  Post failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Post Heritage Canon content to X")
    parser.add_argument("--book", help="Only drafts for this book slug")
    parser.add_argument("--dry", action="store_true", help="Print drafts, don't post")
    args = parser.parse_args()

    config = load_config()
    catalog = load_catalog()

    if not args.dry:
        client = get_client(config)
    else:
        client = None

    # Try to load from latest promote.py output; fall back to evergreen drafts
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.glob("promotion_*.md")):
        promo_text = load_drafts(args.book)
        drafts = extract_x_drafts(promo_text, catalog, args.book)
        if not drafts:
            print("No X-ready drafts in promotion output — using evergreen fallback.")
            drafts = generate_simple_drafts(catalog, args.book)
    else:
        print("No promotion output found — using evergreen drafts.")
        drafts = generate_simple_drafts(catalog, args.book)

    interactive_post(drafts, client, dry_run=args.dry)


if __name__ == "__main__":
    main()
