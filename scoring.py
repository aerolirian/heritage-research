"""
Scoring and ranking layer — merges candidates from all sources, deduplicates,
and produces a ranked list by cultural signal strength.
"""
from collections import defaultdict

# Signal weights (higher = more urgent)
SOURCE_WEIGHTS = {
    "tmdb": 80,      # upcoming film/TV adaptation — strongest urgency
    "reddit": 50,    # social discussion velocity
    "gutenberg": 40, # sustained download demand
    "trends": 45,    # search momentum spike
    "hn": 35,        # intellectual discourse
    "brave": 30,     # news/op-ed mentions
    "goodreads": 35, # reader-driven list traction
}

KNOWN_CATALOG = {
    # author last name → (full_name, canonical_title)
    "Mann": ("Thomas Mann", "Buddenbrooks"),
    "Kafka": ("Franz Kafka", "The Trial"),
    "Joyce": ("James Joyce", "A Portrait of the Artist as a Young Man"),
    "Hamsun": ("Knut Hamsun", "Growth of the Soil"),
    "Lewis": ("Sinclair Lewis", "Arrowsmith"),
    "Woolf": ("Virginia Woolf", "Mrs Dalloway"),
    "Fitzgerald": ("F. Scott Fitzgerald", "The Great Gatsby"),
    "Conrad": ("Joseph Conrad", "Heart of Darkness"),
    "Dostoevsky": ("Fyodor Dostoevsky", "Crime and Punishment"),
    "Tolstoy": ("Leo Tolstoy", "Anna Karenina"),
    "Hemingway": ("Ernest Hemingway", "The Sun Also Rises"),
    "Flaubert": ("Gustave Flaubert", "Madame Bovary"),
    "Chekhov": ("Anton Chekhov", "The Cherry Orchard"),
    "Zola": ("Emile Zola", "Germinal"),
}


def score_and_rank(candidates):
    """Merge, deduplicate, score, and rank all candidates."""
    merged = defaultdict(lambda: {
        "author": "",
        "title": "",
        "sources": [],
        "signals": [],
        "score": 0,
        "why_now": "",
        "subtitle_angle": "",
    })

    for c in candidates:
        author = _normalize_author(c.get("author", ""))
        title = c.get("title", "")
        key = author or title

        if not key:
            continue

        entry = merged[key]
        if not entry["author"]:
            entry["author"] = author
        if not entry["title"] and title:
            entry["title"] = title
        if not entry["title"] and author in KNOWN_CATALOG:
            entry["title"] = KNOWN_CATALOG[author][1]

        source = c.get("source", "unknown")
        weight = SOURCE_WEIGHTS.get(source, 20)
        raw = c.get("raw_score", 10)
        entry["score"] += weight + (raw * 0.1)
        entry["sources"].append(source)

        why = c.get("why_now", "")
        if why and why not in entry["signals"]:
            entry["signals"].append(why)

        # Use highest-priority why_now
        if source == "tmdb" or not entry["why_now"]:
            entry["why_now"] = why

    result = list(merged.values())

    # Bonus for multi-source corroboration
    for entry in result:
        unique_sources = len(set(entry["sources"]))
        if unique_sources >= 3:
            entry["score"] *= 1.5
        elif unique_sources >= 2:
            entry["score"] *= 1.2

    result.sort(key=lambda x: x["score"], reverse=True)
    return result


def _normalize_author(author):
    if not author:
        return ""
    # Map last names to full names
    for last, (full, _) in KNOWN_CATALOG.items():
        if last.lower() == author.lower() or full.lower() == author.lower():
            return full
    return author
