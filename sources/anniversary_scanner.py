"""
Anniversary calendar — publication centennials and literary milestones.
100-year anniversaries drive media coverage, educational focus, cultural moments.
A centennial = a defined window to be first with the philosophical edition.
No API needed — pure date calculation.
"""
from datetime import date

CURRENT_YEAR = date.today().year

# Catalog of significant PD works with first publication year.
# Format: (author, title, year, gutenberg_id_or_None)
# Covers life+70 public domain territory (author death <1955)
WORKS_CATALOG = [
    # 1920s works (centennials 2020-2029)
    ("Sinclair Lewis",       "Main Street",                   1920, 543),
    ("Edith Wharton",        "The Age of Innocence",          1920, 541),
    ("D.H. Lawrence",        "Women in Love",                 1920, 4240),
    ("F. Scott Fitzgerald",  "This Side of Paradise",         1920, 805),
    ("Sinclair Lewis",       "Babbitt",                       1922, 1156),
    ("T.S. Eliot",           "The Waste Land",                1922, None),
    ("James Joyce",          "Ulysses",                       1922, None),
    ("Willa Cather",         "One of Ours",                   1922, None),
    ("Rainer Maria Rilke",   "Sonnets to Orpheus",            1922, None),
    ("Franz Kafka",          "The Trial",                     1925, None),
    ("Theodor Dreiser",      "An American Tragedy",           1925, None),
    ("Virginia Woolf",       "Mrs Dalloway",                  1925, None),
    ("F. Scott Fitzgerald",  "The Great Gatsby",              1925, 64317),
    ("Ernest Hemingway",     "The Sun Also Rises",            1926, None),
    ("Franz Kafka",          "The Castle",                    1926, None),
    ("Virginia Woolf",       "To the Lighthouse",             1927, None),
    ("Sinclair Lewis",       "Elmer Gantry",                  1927, None),
    ("D.H. Lawrence",        "Lady Chatterley's Lover",       1928, None),
    ("Knut Hamsun",          "Wayfarers",                     1927, None),
    ("Thomas Mann",          "The Magic Mountain",            1924, None),
    ("Thomas Wolfe",         "Look Homeward, Angel",          1929, None),
    ("Ernest Hemingway",     "A Farewell to Arms",            1929, None),
    ("William Faulkner",     "The Sound and the Fury",        1929, None),
    # 1930s works (centennials 2030-2039) — near future
    ("Sinclair Lewis",       "It Can't Happen Here",          1935, None),
    ("William Faulkner",     "As I Lay Dying",                1930, None),
    ("John Steinbeck",       "Of Mice and Men",               1937, None),
    ("Mikhail Bulgakov",     "The Master and Margarita",      1967, None),  # written 1930s
]

WINDOW_YEARS = 2  # flag if centennial is within this many years


def scan(config):
    candidates = []

    for author, title, pub_year, gutenberg_id in WORKS_CATALOG:
        centennial = pub_year + 100
        years_away = centennial - CURRENT_YEAR

        if abs(years_away) <= WINDOW_YEARS:
            if years_away > 0:
                timing = f"centennial in {years_away} year{'s' if years_away > 1 else ''} ({centennial})"
                urgency = 70 + (WINDOW_YEARS - years_away) * 10
            elif years_away == 0:
                timing = f"centennial THIS YEAR ({centennial})"
                urgency = 95
            else:
                timing = f"centennial was {abs(years_away)} year{'s' if abs(years_away) > 1 else ''} ago ({centennial})"
                urgency = 50

            candidates.append({
                "source": "anniversary",
                "author": author,
                "title": title,
                "publication_year": pub_year,
                "centennial_year": centennial,
                "years_away": years_away,
                "gutenberg_id": gutenberg_id,
                "why_now": f"Publication {timing} — media coverage window",
                "raw_score": urgency,
            })

    # Sort by urgency (closest centennial first)
    candidates.sort(key=lambda x: abs(x["years_away"]))
    return candidates
