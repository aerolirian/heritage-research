"""
PD entry scanner — surfaces works that enter public domain THIS year or next year.

EU rule:  author died in (current_year - 70) → PD from Jan 1 this year
US rule:  published in (current_year - 95) → PD from Jan 1 this year

Works entering PD represent a new publishing opportunity that didn't exist last year.
The window is tight — other publishers notice too — so urgency is high.

No API needed. Pure date arithmetic against a curated catalog.
"""
from datetime import date

CURRENT_YEAR = date.today().year

# (author, title, death_year, pub_year, gutenberg_id_or_None)
# death_year drives EU PD; pub_year drives US PD.
# Include works where either threshold fires within WINDOW_YEARS.
WORKS_CATALOG = [
    # Authors dying 1950–1960 (EU PD 2020–2030)
    ("George Bernard Shaw",   "Pygmalion",                        1950, 1916, 3825),
    ("George Bernard Shaw",   "Heartbreak House",                 1950, 1919, None),
    ("George Bernard Shaw",   "Saint Joan",                       1950, 1923, None),
    ("George Orwell",         "Nineteen Eighty-Four",             1950, 1949, None),
    ("George Orwell",         "Animal Farm",                      1950, 1945, None),
    ("André Gide",            "The Immoralist",                   1951, 1902, None),
    ("Knut Hamsun",           "Hunger",                           1952, 1890, None),
    ("Knut Hamsun",           "Pan",                              1952, 1894, None),
    ("Hilaire Belloc",        "The Path to Rome",                 1953, 1902, None),
    ("Dylan Thomas",          "Do not go gentle into that good night", 1953, 1951, None),
    ("Colette",               "Gigi",                             1954, 1944, None),
    ("Colette",               "The Vagabond",                     1954, 1910, None),
    ("Thomas Mann",           "The Magic Mountain",               1955, 1924, None),
    ("Thomas Mann",           "Tonio Kröger",                     1955, 1903, None),
    ("Thomas Mann",           "Doctor Faustus",                   1955, 1947, None),
    ("Albert Einstein",       "Relativity",                       1955, 1916, None),
    ("Teilhard de Chardin",   "The Phenomenon of Man",            1955, 1955, None),
    ("H.L. Mencken",          "The American Language",            1956, 1919, None),
    ("Bertolt Brecht",        "Mother Courage and Her Children",  1956, 1941, None),
    ("Bertolt Brecht",        "The Threepenny Opera",             1956, 1928, None),
    ("Walter de la Mare",     "Memoirs of a Midget",              1956, 1921, None),
    ("Joseph McCarthy",       "McCarthyism",                      1957, 1952, None),  # skip — no literary value
    ("Rex Warner",            "The Aerodrome",                    1986, 1941, None),
    ("Wyndham Lewis",         "Tarr",                             1957, 1918, None),
    ("Dorothy L. Sayers",     "Gaudy Night",                      1957, 1935, None),
    ("Giuseppe Tomasi di Lampedusa", "The Leopard",               1957, 1958, None),
    ("Boris Pasternak",       "Doctor Zhivago",                   1960, 1957, None),
    ("Albert Camus",          "The Stranger",                     1960, 1942, None),
    ("Albert Camus",          "The Plague",                       1960, 1947, None),
    ("Albert Camus",          "The Myth of Sisyphus",             1960, 1942, None),
    # US PD entries — published 1928–1935 (PD 2023–2030)
    ("D.H. Lawrence",         "Lady Chatterley's Lover",          1930, 1928, None),
    ("William Faulkner",      "The Sound and the Fury",           1962, 1929, None),
    ("Ernest Hemingway",      "A Farewell to Arms",               1961, 1929, None),
    ("Thomas Wolfe",          "Look Homeward, Angel",             1938, 1929, None),
    ("Erich Maria Remarque",  "All Quiet on the Western Front",   1970, 1929, None),
    ("William Faulkner",      "As I Lay Dying",                   1962, 1930, None),
    ("Dashiell Hammett",      "The Maltese Falcon",               1961, 1930, None),
    ("Dashiell Hammett",      "The Glass Key",                    1961, 1931, None),
    ("Pearl S. Buck",         "The Good Earth",                   1973, 1931, None),
    ("Aldous Huxley",         "Brave New World",                  1963, 1932, None),
    ("Erskine Caldwell",      "Tobacco Road",                     1987, 1932, None),
    ("Nathanael West",        "Miss Lonelyhearts",                1940, 1933, None),
    ("Henry Miller",          "Tropic of Cancer",                 1980, 1934, None),
    ("F. Scott Fitzgerald",   "Tender Is the Night",              1940, 1934, None),
    ("Henry Roth",            "Call It Sleep",                    1995, 1934, None),
    ("Sinclair Lewis",        "It Can't Happen Here",             1951, 1935, None),
    ("Flannery O'Connor",     "A Good Man Is Hard to Find",       1964, 1955, None),
]

WINDOW_YEARS = 1  # flag current year and next year only


def scan(config):
    candidates = []

    for entry in WORKS_CATALOG:
        author, title, death_year, pub_year, gutenberg_id = entry

        # PD entry year = first calendar year in which the work is free.
        # EU: protection expires Dec 31 of (death_year + 70) → PD from Jan 1 of (death_year + 71)
        # US: protection runs 95 years from publication → PD from Jan 1 of (pub_year + 96)
        eu_pd_year = death_year + 71
        us_pd_year = pub_year + 96

        reasons = []

        if 0 <= eu_pd_year - CURRENT_YEAR <= WINDOW_YEARS:
            if eu_pd_year == CURRENT_YEAR:
                reasons.append(f"entered EU public domain this year ({author} d.{death_year})")
            else:
                reasons.append(f"enters EU public domain next year ({author} d.{death_year})")

        if 0 <= us_pd_year - CURRENT_YEAR <= WINDOW_YEARS:
            if us_pd_year == CURRENT_YEAR:
                reasons.append(f"entered US public domain this year (pub. {pub_year})")
            else:
                reasons.append(f"enters US public domain next year (pub. {pub_year})")

        if not reasons:
            continue

        # Urgency: current year fires higher than next year
        urgency = 85 if any("this year" in r for r in reasons) else 65
        # Both US+EU firing together = stronger signal
        if len(reasons) == 2:
            urgency = min(urgency + 10, 95)

        candidates.append({
            "source": "pd_entry",
            "author": author,
            "title": title,
            "death_year": death_year,
            "pub_year": pub_year,
            "gutenberg_id": gutenberg_id,
            "why_now": "; ".join(r.capitalize() for r in reasons),
            "raw_score": urgency,
        })

    candidates.sort(key=lambda x: x["raw_score"], reverse=True)
    return candidates
