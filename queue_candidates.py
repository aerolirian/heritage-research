#!/usr/bin/env python3
"""
queue_candidates.py — Promote research candidates into the production book_list.csv.

Reads output/candidates.json (from `python research.py sweep`), filters out titles
already in book_list.csv, computes a production priority score for each new entry,
and inserts them into the CSV. The CSV is then re-sorted:

  1. In-progress rows (any V in tracking columns) — original order preserved
  2. Queued rows (no V's) — sorted by priority_score descending

Priority score formula:
  base   = research signal score (0–4000)
  × 0.6  if same author already has ≥2 books in pipeline  (saturation)
  × 0.85 if same author already has 1 book
  × 0.8  if author died after 1954  (complex copyright, restricted territories)
  × 1.15 if Novella or ShortStories  (faster to produce)
  × 1.1  if film/TV adaptation signal present (urgency window)
  × 1.05 if subtitle_angle is non-empty (brief already has a hook)

Usage:
    cd /home/ubuntu/heritage-research
    python queue_candidates.py             # dry run — show what would be added
    python queue_candidates.py --apply     # write to book_list.csv
    python queue_candidates.py --top 30    # consider top N candidates (default 50)
    python queue_candidates.py --resort    # just re-sort existing CSV, don't add rows
"""
import argparse
import csv
import json
import re
import time
from pathlib import Path

import requests

GDRIVE_ROOT   = Path("/home/ubuntu/gdrive/heritage_audiobooks")
BOOKS_DIR     = GDRIVE_ROOT / "books"
CSV_PATH      = GDRIVE_ROOT / "book_list.csv"
CANDIDATES    = Path("output/candidates.json")

# Known author death years — fallback when Wikidata lookup fails.
# Only list authors where we need to enforce non-PD filtering.
KNOWN_DEATH_YEARS: dict[str, int] = {
    "George Orwell": 1950,
    "Ernest Hemingway": 1961,
    "Albert Camus": 1960,
    "Aldous Huxley": 1963,
    "Ayn Rand": 1982,
    "C.S. Lewis": 1963,
    "J.R.R. Tolkien": 1973,
    "J.M. Barrie": 1937,
    "Virginia Woolf": 1941,
    "Franz Kafka": 1924,
    "Friedrich Nietzsche": 1900,
    "Oscar Wilde": 1900,
    "Leo Tolstoy": 1910,
    "Anton Chekhov": 1904,
    "Fyodor Dostoevsky": 1881,
    "Gustave Flaubert": 1880,
    "Victor Hugo": 1885,
    "Alexandre Dumas": 1870,
    "Thomas Hardy": 1928,
    "Joseph Conrad": 1924,
    "D.H. Lawrence": 1930,
    "Marcel Proust": 1922,
    "Hermann Hesse": 1962,
    "William Faulkner": 1962,
    "F. Scott Fitzgerald": 1940,
    "Sinclair Lewis": 1951,
    "Knut Hamsun": 1952,
    "Thomas Mann": 1955,
    "Stefan Zweig": 1942,
    "Sigrid Undset": 1949,
    "Robert Louis Stevenson": 1894,
    "Arthur Conan Doyle": 1930,
    "H.G. Wells": 1946,
    "H.P. Lovecraft": 1937,
    "Algernon Blackwood": 1951,
    "Arthur Machen": 1947,
    "Lord Dunsany": 1957,
    "James Joyce": 1941,
    "William Shakespeare": 1616,
    "Jane Austen": 1817,
    "Charlotte Brontë": 1855,
    "Emily Brontë": 1848,
    "Charles Dickens": 1870,
    "Herman Melville": 1891,
    # Still in copyright
    "Agatha Christie": 1976,
    "Arthur Miller": 2005,
    "William Golding": 1993,
    "John Steinbeck": 1968,
    "Ray Bradbury": 2012,
    "Harper Lee": 2016,
    "J.D. Salinger": 2010,
    "Jean-Paul Sartre": 1980,
    "Albert Camus": 1960,
    "Simone de Beauvoir": 1986,
    "Samuel Beckett": 1989,
    "Milan Kundera": 2023,
    "Daniel Quinn": 2018,
    "Jostein Gaarder": 2099,   # still alive
    "Paulo Coelho": 2099,      # still alive
    "Matt Haig": 2099,         # still alive
    "Willy Russell": 2099,     # still alive
    "Mitch Albom": 2099,       # still alive
    "Ian McEwan": 2099,        # still alive
    "Philip Pullman": 2099,    # still alive
    "Antoine de Saint-Exupéry": 1944,
    "Antoine de Saint-Exup\u00e9ry": 1944,
}

TRACKING_COLS = [
    "gutenberg_found", "gutenberg_id", "epub_downloaded", "cover_image",
    "cover_art", "introduction", "heritage_epub", "json", "normalized",
    "prep_complete", "tts_approved", "tts_complete", "m4b_approved",
    "m4b_complete", "epub_approved",
]

# Genres that map to shorter production time
SHORT_GENRES = {"Novella", "ShortStories"}

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def clean_title(t: str) -> str:
    """Strip Goodreads-style format/edition suffixes from titles."""
    # Remove trailing parentheticals like "(Paperback)", "(Mass Market Paperback)", "(Hardcover)"
    t = re.sub(r"\s*\((Paperback|Hardcover|Mass Market Paperback|Kindle|Ebook|Audio|Audiobook"
               r"|Annotated|Illustrated|Classic|Edition|Volume \d+|#\d+[^)]*)\)\s*$",
               "", t, flags=re.IGNORECASE)
    # Remove series identifiers like "(Chronicles of Narnia, #5)"
    t = re.sub(r"\s*\([^)]+,\s*#\d+\)\s*$", "", t)
    return t.strip()


def normalize_title(t: str) -> str:
    """Lowercase, strip articles and punctuation for fuzzy matching."""
    t = clean_title(t).lower().strip()
    t = re.sub(r"^(the |a |an )", "", t)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return t.strip()


def is_public_domain(death_year) -> bool:
    """True if author is clearly PD in major territories (life+70 years)."""
    if death_year is None:
        return True  # unknown — let it through, user can review
    try:
        return int(death_year) + 70 < 2026
    except (ValueError, TypeError):
        return True


def is_in_progress(row: dict) -> bool:
    """True if any pipeline tracking column has a V."""
    return any(row.get(col, "").strip() == "V" for col in TRACKING_COLS)


def author_last(name: str) -> str:
    parts = name.strip().split()
    return parts[-1].lower() if parts else ""


# -------------------------------------------------------------------------
# Enrichment: author death year + first publication year
# -------------------------------------------------------------------------

def enrich_from_books_dir(title: str, author: str) -> dict:
    """
    Check if this title already exists in the books/ directory and pull
    metadata from book.json.
    """
    norm = normalize_title(title)
    for book_json in BOOKS_DIR.glob("*/book.json"):
        try:
            data = json.loads(book_json.read_text())
        except Exception:
            continue
        if normalize_title(data.get("title", "")) == norm:
            return {
                "death_year": data.get("author_death_year"),
                "pub_year":   data.get("first_publication_year", ""),
                "genre":      data.get("genre", "Novel"),
            }
    return {}


def enrich_from_wikidata(author: str) -> dict:
    """
    Look up author death year from Wikidata using the entity search + claims API.
    Returns {} on failure.
    """
    try:
        # Step 1: search for the author entity
        r = requests.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": author,
                "type": "item",
                "language": "en",
                "format": "json",
                "limit": 5,
            },
            timeout=10,
        )
        results = r.json().get("search", [])
        if not results:
            return {}

        # Pick the first result that has "human" in description
        entity_id = None
        for res in results:
            desc = res.get("description", "").lower()
            if any(w in desc for w in ("novelist", "writer", "author", "poet", "playwright", "human")):
                entity_id = res["id"]
                break
        if not entity_id:
            entity_id = results[0]["id"]

        # Step 2: fetch P570 (date of death)
        r2 = requests.get(
            f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json",
            timeout=10,
        )
        claims = r2.json().get("entities", {}).get(entity_id, {}).get("claims", {})
        death_claims = claims.get("P570", [])
        if death_claims:
            raw = death_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
            time_str = raw.get("time", "")  # e.g. "+1955-08-12T00:00:00Z"
            if time_str:
                year = int(time_str.lstrip("+").split("-")[0])
                return {"death_year": year}

        time.sleep(0.5)  # be polite
    except Exception:
        pass

    return {}


def infer_genre(candidate: dict) -> str:
    """
    Infer PrimaryGenre from signals or default to Novel.
    """
    signals_text = " ".join(candidate.get("signals", [])).lower()
    title_lower  = candidate.get("title", "").lower()

    if any(w in signals_text for w in ("short story", "short stories", "collection")):
        return "ShortStories"
    if any(w in signals_text for w in ("novella",)):
        return "Novella"
    if any(w in title_lower for w in ("metamorphosis",)):
        return "Novella"
    if any(w in signals_text for w in ("horror", "gothic horror")):
        return "Horror"
    if any(w in signals_text for w in ("fantasy", "fairy tale", "faerie")):
        return "Fantasy"
    if any(w in signals_text for w in ("science fiction", "sci-fi", "dystopia")):
        return "ScienceFiction"
    return "Novel"


# -------------------------------------------------------------------------
# Priority score
# -------------------------------------------------------------------------

def compute_priority(candidate: dict, author_count_in_pipeline: int, death_year) -> float:
    score = candidate.get("score", 0.0)

    # Author saturation
    if author_count_in_pipeline >= 2:
        score *= 0.6
    elif author_count_in_pipeline == 1:
        score *= 0.85

    # Copyright complexity: author died after 1954 → not yet globally PD
    if death_year is not None:
        try:
            dy = int(death_year)
            if dy > 1954:
                score *= 0.8
        except (ValueError, TypeError):
            pass

    # Short work bonus
    genre = infer_genre(candidate)
    if genre in SHORT_GENRES:
        score *= 1.15

    # Film/TV adaptation urgency
    if any("tmdb" in s or "film" in s.lower() or "adaptation" in s.lower()
           for s in candidate.get("sources", [])):
        score *= 1.1

    # Hook ready
    if candidate.get("subtitle_angle", "").strip():
        score *= 1.05

    return round(score, 1)


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

def load_csv() -> tuple[list[str], list[dict]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    return fieldnames, rows


def save_csv(fieldnames: list[str], rows: list[dict]) -> None:
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sort_rows(rows: list[dict]) -> list[dict]:
    """
    Sort rows:
      1. In-progress (any V in tracking cols) — stable sort by original index
      2. Queued (no V's) — sorted by priority_score descending, then original index
    """
    in_progress = [(i, r) for i, r in enumerate(rows) if is_in_progress(r)]
    queued      = [(i, r) for i, r in enumerate(rows) if not is_in_progress(r)]

    def queue_key(item):
        i, r = item
        try:
            ps = float(r.get("priority_score", 0) or 0)
        except ValueError:
            ps = 0.0
        return (-ps, i)  # descending score, stable by original position

    in_progress.sort(key=lambda x: x[0])
    queued.sort(key=queue_key)

    return [r for _, r in in_progress] + [r for _, r in queued]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply",  action="store_true", help="Write to book_list.csv (default: dry run)")
    parser.add_argument("--top",    type=int, default=50, help="Consider top N candidates (default 50)")
    parser.add_argument("--resort", action="store_true", help="Re-sort existing CSV without adding new rows")
    args = parser.parse_args()

    if not CANDIDATES.exists():
        print("No candidates.json found. Run: python research.py sweep")
        return

    candidates = json.loads(CANDIDATES.read_text())
    fieldnames, rows = load_csv()

    # Add priority_score column if missing
    if "priority_score" not in fieldnames:
        # Insert after PrimaryGenre (5th column)
        idx = fieldnames.index("PrimaryGenre") + 1
        fieldnames.insert(idx, "priority_score")
        for r in rows:
            r.setdefault("priority_score", "")

    # Assign default scores to existing queued rows that have no score yet.
    # Preserves editorial intent: earlier position = higher score.
    # Range: 50 (bottom of existing queue) to 500 (top of existing queue).
    unscored_queued = [r for r in rows if not is_in_progress(r) and not r.get("priority_score", "").strip()]
    n = len(unscored_queued)
    if n:
        for i, r in enumerate(unscored_queued):
            # Linear: first row gets 500, last gets 50
            r["priority_score"] = str(round(500 - (450 * i / max(n - 1, 1)), 1))

    if args.resort:
        rows = sort_rows(rows)
        if args.apply:
            save_csv(fieldnames, rows)
            print(f"Re-sorted {len(rows)} rows → {CSV_PATH}")
        else:
            in_prog = sum(1 for r in rows if is_in_progress(r))
            queued  = len(rows) - in_prog
            print(f"DRY RUN: would re-sort {len(rows)} rows ({in_prog} in-progress, {queued} queued)")
        return

    # Build lookup of existing titles in CSV
    existing_titles = {normalize_title(r["Title"]) for r in rows}

    # Count author representation in pipeline (in-progress + queued)
    author_pipeline_count: dict[str, int] = {}
    for r in rows:
        last = author_last(r.get("Author", ""))
        author_pipeline_count[last] = author_pipeline_count.get(last, 0) + 1

    print(f"book_list.csv: {len(rows)} existing titles")
    print(f"Candidates: {len(candidates)} total, considering top {args.top}\n")

    new_rows = []
    skipped_existing = 0
    skipped_no_title = 0

    for c in candidates[:args.top]:
        title  = c.get("title", "").strip()
        author = c.get("author", "").strip()

        if not title or not author:
            skipped_no_title += 1
            continue

        # Clean Goodreads format labels from title
        title = clean_title(title)

        if normalize_title(title) in existing_titles:
            skipped_existing += 1
            continue

        # Enrich: books/ dir → hardcoded dict → Wikidata
        info = enrich_from_books_dir(title, author)
        if not info.get("death_year"):
            if author in KNOWN_DEATH_YEARS:
                info["death_year"] = KNOWN_DEATH_YEARS[author]
            else:
                wd = enrich_from_wikidata(author)
                info.update(wd)

        death_year = info.get("death_year")
        pub_year   = str(info.get("pub_year", "")).strip()
        genre      = info.get("genre") or infer_genre(c)

        # Skip books that aren't yet public domain (life+70)
        if not is_public_domain(death_year):
            print(f"  - {title} ({author})  SKIP: not PD (d.{death_year})")
            skipped_existing += 1
            continue

        a_last = author_last(author)
        author_count = author_pipeline_count.get(a_last, 0)
        priority = compute_priority(c, author_count, death_year)

        row = {
            "Title":                 title,
            "Author":                author,
            "FirstPublicationYear":  pub_year,
            "AuthorDeathYear":       str(death_year) if death_year else "",
            "PrimaryGenre":          genre,
            "priority_score":        str(priority),
            # All tracking cols empty
            **{col: "" for col in TRACKING_COLS},
            # Copyright territory cols (blank — copyright.py fills these)
            **{k: "" for k in fieldnames
               if k not in ("Title", "Author", "FirstPublicationYear",
                            "AuthorDeathYear", "PrimaryGenre", "priority_score")
               and k not in TRACKING_COLS},
        }

        new_rows.append((priority, row))
        author_pipeline_count[a_last] = author_count + 1

        why = c.get("why_now", "")[:70]
        print(f"  + {title} ({author})  score={priority}  [{why}]")

    print(f"\nSummary: {len(new_rows)} new, {skipped_existing} already in CSV, "
          f"{skipped_no_title} skipped (no title/author)")

    if not new_rows:
        print("Nothing to add.")
        return

    # Add new rows to master list and re-sort
    all_rows = rows + [r for _, r in new_rows]
    sorted_rows = sort_rows(all_rows)

    # Preview top 20 queued
    queued = [r for r in sorted_rows if not is_in_progress(r)]
    print(f"\nTop 20 queued after merge (by priority_score):")
    for i, r in enumerate(queued[:20], 1):
        ps = r.get("priority_score", "")
        print(f"  {i:>2}. [{ps:>8}]  {r['Title']} — {r['Author']}")

    if not args.apply:
        print(f"\nDRY RUN — run with --apply to write {len(sorted_rows)} rows to {CSV_PATH}")
        return

    save_csv(fieldnames, sorted_rows)
    print(f"\nWrote {len(sorted_rows)} rows to {CSV_PATH}")
    print(f"  Added: {len(new_rows)}  |  In-progress: {sum(1 for r in sorted_rows if is_in_progress(r))}"
          f"  |  Queued: {len(queued)}")


if __name__ == "__main__":
    main()
