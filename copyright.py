"""
Public domain status checker by territory.
Mirrors the copyright.py logic from the publishing pipeline.
"""

# Life+N terms by country group
TERRITORY_TERMS = {
    70: ["US", "GB", "DE", "FR", "ES", "IT", "NL", "PL", "SE", "NO", "DK",
         "FI", "AT", "CH", "BE", "PT", "GR", "CZ", "HU", "RO", "AU", "NZ",
         "CA", "JP", "KR", "BR", "AR", "CL", "PE", "VE", "ZA", "NG", "KE"],
    80: ["CO", "BO"],
    95: ["CI"],
    99: ["JM"],
    100: ["MX"],
    60: ["IN", "BD", "LK"],
    50: ["CN", "PK", "MY", "TH", "EG"],
}

CURRENT_YEAR = 2026


def check_pd(author_name, death_year):
    """Return PD status per territory group for an author."""
    restricted = []
    allowed = []

    for term, countries in TERRITORY_TERMS.items():
        if death_year + term < CURRENT_YEAR:
            allowed.extend(countries)
        else:
            restricted.extend(countries)

    mode = "include" if len(restricted) > 20 else "exclude"

    return {
        "author": author_name,
        "death_year": death_year,
        "year_calculated": CURRENT_YEAR,
        "mode": mode,
        "territories": restricted if mode == "exclude" else allowed,
        "notes": (
            f"Author d.{death_year}; "
            f"Restricted in: {', '.join(restricted)}" if restricted
            else f"Author d.{death_year}; PD in all monitored territories"
        ),
    }
