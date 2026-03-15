"""
Scoring and ranking layer — merges candidates from all sources, deduplicates,
and produces a ranked list by cultural signal strength.
"""
from collections import defaultdict

# Signal weights (higher = more urgent)
SOURCE_WEIGHTS = {
    "tmdb": 80,          # upcoming film/TV adaptation — strongest urgency
    "anniversary": 70,   # centennial — defined media window, now or never
    "wikipedia": 65,     # traffic spike = something just happened culturally
    "reddit": 50,        # social discussion velocity
    "trends": 45,        # search momentum spike
    "gutenberg": 40,     # sustained download demand
    "youtube": 40,       # video essay = intellectual resurgence, HC audience
    "goodreads": 35,     # reader-driven list traction
    "hn": 35,            # intellectual discourse
    "letterboxd": 35,    # film-literary audience overlap
    "opensyllabus": 35,  # institutional/academic teaching signal
    "tiktok": 30,        # booktok organic traction
    "brave": 30,         # news/op-ed mentions
    "instagram": 25,     # aesthetic/visual traction
    "amazon": 25,        # competitor gap analysis
    "twitter": 25,       # discourse signal
    # Reader congregation platforms
    "marginalian": 50,   # Maria Popova essay = HC demographic primed
    "podcast": 45,       # dedicated episode = 30-60min audience immersion
    "lithub": 45,        # biggest literary publication — what serious readers see
    "fivebooks": 40,     # expert recommendation = intellectual legitimacy
    "librarything": 38,  # serious literary catalogers
    "substack": 38,      # literary newsletter engagement
    "openlibrary": 35,   # actual reader demand (borrow/readinglog counts)
    "storygraph": 35,    # growing GR alternative, younger literary audience
    "stackexchange": 35, # close reading = deep engagement signal
    "bookbub": 30,       # commercial demand signal
    "tumblr": 28,        # younger readers discovering classics
    "quora": 25,         # intent signal (what readers are searching for)
    "omdb": 30,          # adaptation quality data — intro critique ammunition
    "googlebooks": 20,   # competitor edition gap analysis
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

# Title → author lookup so TMDB/title-only candidates merge with author-keyed entries
# Permanent adaptation legacy bonus — titles with major established film/TV adaptations
# that predate TMDB's 180-day window. Applied after multi-source bonus.
# Values are flat score additions (on top of base score) reflecting adaptation weight.
KNOWN_ADAPTATIONS = {
    "1984":                        150,  # 1984 film (1984), BBC dramatisations; defining cultural touchstone
    "nineteen eighty-four":        150,
    "crime and punishment":        100,  # Raskolnikov is cinema shorthand; multiple major films
    "les misérables":              120,  # 2012 musical film ($440M global), 2018 BBC miniseries
    "les miserables":              120,
    "lady chatterley's lover":     100,  # 2022 Netflix film (Emma Corrin) — very recent
    "romeo and juliet":            130,  # Baz Luhrmann 1996 ($147M), 2013 film, countless versions
    "a christmas carol":            90,  # Muppets, Scrooge (1951), countless remakes every decade
    "anna karenina":                90,  # 2012 Keira Knightley film; Tolstoy's most adapted novel
    "war and peace":                80,  # 2016 BBC miniseries; perennial TV event
    "wuthering heights":            80,  # 2011 Andrea Arnold; multiple major versions
    "the great gatsby":             90,  # 2013 Baz Luhrmann ($352M); definitive American adaptation
    "dracula":                      70,  # Lugosi, Langella, Coppola, BBC 2020 series
    "frankenstein":                 70,  # Universal, Branagh, Shelley canon
    "the picture of dorian gray":   70,  # 2009 film; theatrical adaptations ongoing
    "the count of monte cristo":    90,  # 2024 French film ($65M+); Alexandre de la Pattellière
    "the odyssey":                  80,  # 2025 Christopher Nolan film announced; Coen Bros interest
    "the jungle book":              80,  # 2016 Favreau ($966M), multiple Disney versions
    "heart of darkness":            70,  # Apocalypse Now (1979) — indirect but massive
    "madame bovary":                70,  # 2014 film; multiple French versions
    "the sun also rises":           60,  # 1957 Tyrone Power film; Hemingway cinema legacy
}

TITLE_AUTHOR_MAP = {
    "wuthering heights": "Emily Brontë",
    "jane eyre": "Charlotte Brontë",
    "the odyssey": "Homer",
    "frankenstein": "Mary Shelley",
    "dracula": "Bram Stoker",
    "crime and punishment": "Fyodor Dostoevsky",
    "anna karenina": "Leo Tolstoy",
    "war and peace": "Leo Tolstoy",
    "the death of ivan ilych": "Leo Tolstoy",
    "madame bovary": "Gustave Flaubert",
    "the great gatsby": "F. Scott Fitzgerald",
    "the sun also rises": "Ernest Hemingway",
    "a farewell to arms": "Ernest Hemingway",
    "the old man and the sea": "Ernest Hemingway",
    "death in venice": "Thomas Mann",
    "the magic mountain": "Thomas Mann",
    "buddenbrooks": "Thomas Mann",
    "the trial": "Franz Kafka",
    "the metamorphosis": "Franz Kafka",
    "ulysses": "James Joyce",
    "mrs dalloway": "Virginia Woolf",
    "to the lighthouse": "Virginia Woolf",
    "doctor jekyll": "Robert Louis Stevenson",
    "the picture of dorian gray": "Oscar Wilde",
    "les misérables": "Victor Hugo",
    "the count of monte cristo": "Alexandre Dumas",
    "the sound and the fury": "William Faulkner",
    "as i lay dying": "William Faulkner",
    "heart of darkness": "Joseph Conrad",
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
        # If no author, try to resolve from title (e.g. TMDB candidates)
        if not author and title:
            author = TITLE_AUTHOR_MAP.get(title.lower().split(" (")[0], "")
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

    # Permanent adaptation legacy bonus — established film/TV history
    for entry in result:
        title_key = entry.get("title", "").lower().split(" (")[0].strip()
        bonus = KNOWN_ADAPTATIONS.get(title_key, 0)
        if bonus:
            entry["score"] += bonus
            if "adaptation legacy" not in entry["signals"]:
                entry["signals"].append("adaptation legacy")

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
