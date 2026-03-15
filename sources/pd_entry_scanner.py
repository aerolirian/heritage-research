"""
PD entry scanner — surfaces works that entered or will enter public domain recently.

EU rule:  author died in year D → PD from Jan 1 of (D + 71)
US rule:  published in year P → PD from Jan 1 of (P + 96)

Window: 2 years back (fresh opportunity, competitors now active) through 1 year forward.
Works that entered PD in 2024 or 2025 are still relatively fresh — most publishers
won't have a quality edition out yet. Urgency decays by year: this year > recent > next.

No API needed. Pure date arithmetic against a curated catalog.
"""
from datetime import date

CURRENT_YEAR = date.today().year

# (author, title, death_year, pub_year, gutenberg_id_or_None)
# death_year drives EU PD; pub_year drives US PD.
# Covers PD entries roughly 2022–2031.
WORKS_CATALOG = [
    # --- EU PD 2022 (died 1951) ---
    ("André Gide",            "The Immoralist",                   1951, 1902, None),
    ("André Gide",            "Strait Is the Gate",               1951, 1909, None),
    ("Sinclair Lewis",        "Babbitt",                          1951, 1922, 1156),
    ("Sinclair Lewis",        "Main Street",                      1951, 1920, 543),
    ("Sinclair Lewis",        "It Can't Happen Here",             1951, 1935, None),

    # --- EU PD 2023 (died 1952) ---
    ("Knut Hamsun",           "Hunger",                           1952, 1890, None),
    ("Knut Hamsun",           "Pan",                              1952, 1894, None),
    ("Knut Hamsun",           "Victoria",                         1952, 1898, None),
    ("Knut Hamsun",           "Growth of the Soil",               1952, 1917, None),

    # --- EU PD 2024 (died 1953) ---
    ("Eugene O'Neill",        "Long Day's Journey into Night",    1953, 1956, None),
    ("Eugene O'Neill",        "Mourning Becomes Electra",         1953, 1931, None),
    ("Eugene O'Neill",        "Strange Interlude",                1953, 1928, None),
    ("Eugene O'Neill",        "The Iceman Cometh",                1953, 1946, None),
    ("Dylan Thomas",          "Under Milk Wood",                  1953, 1954, None),
    ("Dylan Thomas",          "Adventures in the Skin Trade",     1953, 1955, None),
    ("Ivan Bunin",            "The Gentleman from San Francisco", 1953, 1915, None),
    ("Ivan Bunin",            "The Village",                      1953, 1910, None),
    ("Ivan Bunin",            "Dark Avenues",                     1953, 1943, None),
    ("Hilaire Belloc",        "The Path to Rome",                 1953, 1902, None),
    ("Hilaire Belloc",        "The Servile State",                1953, 1912, None),

    # --- EU PD 2025 (died 1954) ---
    ("Colette",               "Chéri",                            1954, 1920, None),
    ("Colette",               "The Vagabond",                     1954, 1910, None),
    ("Colette",               "Gigi",                             1954, 1944, None),
    ("Colette",               "The Cat",                          1954, 1933, None),
    ("Colette",               "Sido",                             1954, 1930, None),

    # --- EU PD 2026 (died 1955) ---
    ("Thomas Mann",           "The Magic Mountain",               1955, 1924, None),
    ("Thomas Mann",           "Tonio Kröger",                     1955, 1903, None),
    ("Thomas Mann",           "Doctor Faustus",                   1955, 1947, None),
    ("Thomas Mann",           "Joseph and His Brothers",          1955, 1943, None),
    ("José Ortega y Gasset",  "The Revolt of the Masses",         1955, 1930, None),
    ("José Ortega y Gasset",  "Meditations on Quixote",           1955, 1914, None),
    ("James Agee",            "A Death in the Family",            1955, 1957, None),
    ("James Agee",            "Let Us Now Praise Famous Men",     1955, 1941, None),
    ("Albert Einstein",       "Relativity",                       1955, 1916, None),
    ("Teilhard de Chardin",   "The Phenomenon of Man",            1955, 1955, None),

    # --- EU PD 2027 (died 1956) ---
    ("H.L. Mencken",          "The American Language",            1956, 1919, None),
    ("Bertolt Brecht",        "Mother Courage and Her Children",  1956, 1941, None),
    ("Bertolt Brecht",        "The Threepenny Opera",             1956, 1928, None),
    ("Bertolt Brecht",        "The Good Person of Szechwan",      1956, 1943, None),
    ("Walter de la Mare",     "Memoirs of a Midget",              1956, 1921, None),
    ("A.A. Milne",            "Winnie-the-Pooh",                  1956, 1926, 836),
    ("A.A. Milne",            "The House at Pooh Corner",         1956, 1928, None),

    # --- EU PD 2028 (died 1957) ---
    ("Wyndham Lewis",         "Tarr",                             1957, 1918, None),
    ("Dorothy L. Sayers",     "Gaudy Night",                      1957, 1935, None),
    ("Giuseppe Tomasi di Lampedusa", "The Leopard",               1957, 1958, None),

    # --- EU PD 2031 (died 1960) ---
    ("Albert Camus",          "The Stranger",                     1960, 1942, None),
    ("Albert Camus",          "The Plague",                       1960, 1947, None),
    ("Albert Camus",          "The Myth of Sisyphus",             1960, 1942, None),
    ("Albert Camus",          "The Fall",                         1960, 1956, None),
    ("Boris Pasternak",       "Doctor Zhivago",                   1960, 1957, None),

    # --- US PD 2023 (published 1927) ---
    ("Virginia Woolf",        "To the Lighthouse",                1941, 1927, None),
    ("Sinclair Lewis",        "Elmer Gantry",                     1951, 1927, None),
    ("Knut Hamsun",           "Wayfarers",                        1952, 1927, None),
    ("Franz Kafka",           "The Castle",                       1924, 1926, None),

    # --- US PD 2024 (published 1928) ---
    ("Virginia Woolf",        "Orlando",                          1941, 1928, None),
    ("D.H. Lawrence",         "Lady Chatterley's Lover",          1930, 1928, None),
    ("Radclyffe Hall",        "The Well of Loneliness",           1943, 1928, None),
    ("Evelyn Waugh",          "Decline and Fall",                 1966, 1928, None),
    ("Aldous Huxley",         "Point Counter Point",              1963, 1928, None),

    # --- US PD 2025 (published 1929) ---
    ("Ernest Hemingway",      "A Farewell to Arms",               1961, 1929, None),
    ("William Faulkner",      "The Sound and the Fury",           1962, 1929, None),
    ("Erich Maria Remarque",  "All Quiet on the Western Front",   1970, 1929, None),
    ("Thomas Wolfe",          "Look Homeward, Angel",             1938, 1929, None),
    ("Sinclair Lewis",        "Dodsworth",                        1951, 1929, None),
    ("Robert Graves",         "Goodbye to All That",              1985, 1929, None),

    # --- US PD 2026 (published 1930) ---
    ("William Faulkner",      "As I Lay Dying",                   1962, 1930, None),
    ("Dashiell Hammett",      "The Maltese Falcon",               1961, 1930, None),

    # --- US PD 2027 (published 1931) ---
    ("Dashiell Hammett",      "The Glass Key",                    1961, 1931, None),
    ("Pearl S. Buck",         "The Good Earth",                   1973, 1931, None),
    ("Eugene O'Neill",        "Mourning Becomes Electra",         1953, 1931, None),

    # --- US PD 2028 (published 1932) ---
    ("Aldous Huxley",         "Brave New World",                  1963, 1932, None),

    # --- US PD 2029 (published 1933) ---
    ("Nathanael West",        "Miss Lonelyhearts",                1940, 1933, None),

    # --- US PD 2030 (published 1934) ---
    ("F. Scott Fitzgerald",   "Tender Is the Night",              1940, 1934, None),
    ("Henry Miller",          "Tropic of Cancer",                 1980, 1934, None),

    # --- US PD 2031 (published 1935) ---
    ("Sinclair Lewis",        "It Can't Happen Here",             1951, 1935, None),
]

LOOKBACK_YEARS = 2   # include entries from this many years ago (still fresh)
FORWARD_YEARS  = 1   # include entries up to this many years ahead


def scan(config):
    candidates = []
    seen = set()  # deduplicate (author, title) pairs — some entries fire on both axes

    for entry in WORKS_CATALOG:
        author, title, death_year, pub_year, gutenberg_id = entry

        # PD entry year = first calendar year in which the work is free.
        # EU: protection expires Dec 31 of (death_year + 70) → PD from Jan 1 of (death_year + 71)
        # US: protection runs 95 years from publication → PD from Jan 1 of (pub_year + 96)
        eu_pd_year = death_year + 71
        us_pd_year = pub_year + 96

        reasons = []
        best_urgency = 0

        for pd_year, label in ((eu_pd_year, "EU"), (us_pd_year, "US")):
            delta = pd_year - CURRENT_YEAR  # negative = past, 0 = this year, positive = future
            if not (-LOOKBACK_YEARS <= delta <= FORWARD_YEARS):
                continue

            if delta < 0:
                yr = pd_year
                reasons.append(f"entered {label} public domain in {yr} — still fresh")
                best_urgency = max(best_urgency, 60 + delta * 5)  # decays with age
            elif delta == 0:
                reasons.append(f"entered {label} public domain this year")
                best_urgency = max(best_urgency, 85)
            else:
                reasons.append(f"enters {label} public domain next year ({pd_year})")
                best_urgency = max(best_urgency, 65)

        if not reasons:
            continue

        key = (author, title)
        if key in seen:
            continue
        seen.add(key)

        # Both axes firing = stronger signal
        if len(reasons) >= 2:
            best_urgency = min(best_urgency + 10, 95)

        candidates.append({
            "source": "pd_entry",
            "author": author,
            "title": title,
            "death_year": death_year,
            "pub_year": pub_year,
            "gutenberg_id": gutenberg_id,
            "why_now": "; ".join(r.capitalize() for r in reasons),
            "raw_score": best_urgency,
        })

    candidates.sort(key=lambda x: x["raw_score"], reverse=True)
    return candidates
