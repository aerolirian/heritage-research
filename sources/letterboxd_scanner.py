"""
Letterboxd scanner — film community's literary adaptation signal.
Letterboxd users are literary-minded film watchers — exact Heritage Canon overlap.

Uses letterboxdpy (github.com/nmcassa/letterboxdpy) — 140 stars, last commit
~Mar 2026, actively maintained. Scrapes public Letterboxd data cleanly.
No API key needed.
"""
from letterboxdpy import movie
from letterboxdpy.search import get_film_slug_from_title

ADAPTATION_SEARCHES = [
    ("Wuthering Heights", "Emily Brontë"),
    ("Crime and Punishment", "Fyodor Dostoevsky"),
    ("Anna Karenina", "Leo Tolstoy"),
    ("Madame Bovary", "Gustave Flaubert"),
    ("The Trial", "Franz Kafka"),
    ("The Great Gatsby", "F. Scott Fitzgerald"),
    ("Death in Venice", "Thomas Mann"),
    ("Mrs Dalloway", "Virginia Woolf"),
    ("The Picture of Dorian Gray", "Oscar Wilde"),
    ("Dracula", "Bram Stoker"),
    ("Frankenstein", "Mary Shelley"),
    ("The Count of Monte Cristo", "Alexandre Dumas"),
    ("Les Misérables", "Victor Hugo"),
    ("Heart of Darkness", "Joseph Conrad"),
    ("The Metamorphosis", "Franz Kafka"),
    ("The Sun Also Rises", "Ernest Hemingway"),
    ("A Farewell to Arms", "Ernest Hemingway"),
    ("The Sound and the Fury", "William Faulkner"),
    ("The Odyssey", "Homer"),
    ("Buddenbrooks", "Thomas Mann"),
]


def scan(config):
    candidates = []

    for title, author in ADAPTATION_SEARCHES:
        try:
            film_slug = get_film_slug_from_title(title)
            if not film_slug:
                continue

            film = movie.Movie(film_slug)
            rating = getattr(film, "rating", None)
            watchers = getattr(film, "watchers", None)
            fans = getattr(film, "fans", None)
            year = getattr(film, "year", "")

            candidates.append({
                "source": "letterboxd",
                "author": author,
                "title": title,
                "adaptation_slug": film_slug,
                "adaptation_year": str(year) if year else "",
                "letterboxd_rating": str(rating) if rating else "",
                "letterboxd_watchers": watchers,
                "letterboxd_fans": fans,
                "letterboxd_url": f"https://letterboxd.com/film/{film_slug}/",
                "why_now": f"Letterboxd: '{title}' — {rating}/5 from {watchers or '?'} watchers, {fans or '?'} fans",
                "raw_score": 35 + (float(rating) * 3 if rating else 0),
            })
        except Exception as e:
            print(f"  [letterboxd/{title}] {e}")

    return candidates
