"""
Letterboxd scanner — film community's literary adaptation signal.
Letterboxd users are literary-minded film watchers — exact Heritage Canon overlap.
Signals: adaptation lists, which literary films are trending, book→film discussions.
"""
from playwright.sync_api import sync_playwright

LISTS_TO_SCAN = [
    ("https://letterboxd.com/films/based-on-book/", "based_on_book"),
    ("https://letterboxd.com/films/based-on-novel/", "based_on_novel"),
]

SEARCH_TERMS = [
    "thomas mann",
    "kafka",
    "james joyce",
    "dostoevsky",
    "tolstoy",
    "knut hamsun",
    "virginia woolf",
    "fitzgerald",
]

AUTHOR_KEYWORDS = [
    ("Mann", "Thomas Mann"), ("Kafka", "Franz Kafka"), ("Joyce", "James Joyce"),
    ("Dostoevsky", "Fyodor Dostoevsky"), ("Tolstoy", "Leo Tolstoy"),
    ("Hamsun", "Knut Hamsun"), ("Woolf", "Virginia Woolf"),
    ("Fitzgerald", "F. Scott Fitzgerald"), ("Conrad", "Joseph Conrad"),
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })

        # Search Letterboxd for each author
        for term in SEARCH_TERMS:
            try:
                encoded = term.replace(" ", "+")
                page.goto(f"https://letterboxd.com/search/films/{encoded}/", timeout=20000)
                page.wait_for_timeout(2000)

                films = page.evaluate("""
                    () => Array.from(document.querySelectorAll('.film-detail'))
                    .slice(0, 10)
                    .map(el => ({
                        title: (el.querySelector('.film-title-wrapper a') || {}).innerText || '',
                        year: (el.querySelector('.film-title-wrapper small') || {}).innerText || '',
                        rating: (el.querySelector('.average-rating') || {}).innerText || '',
                    }))
                    .filter(f => f.title)
                """)

                for film in films:
                    author_match = next(
                        (full for kw, full in AUTHOR_KEYWORDS if kw.lower() in term.lower()),
                        term.title()
                    )
                    candidates.append({
                        "source": "letterboxd",
                        "author": author_match,
                        "title": "",
                        "adaptation_title": film.get("title", ""),
                        "adaptation_year": film.get("year", ""),
                        "letterboxd_rating": film.get("rating", ""),
                        "why_now": f"Letterboxd: adaptation '{film.get('title','')}' ({film.get('year','')}) rated {film.get('rating','')}",
                        "raw_score": 35,
                    })
            except Exception as e:
                print(f"  [letterboxd/{term}] {e}")

        browser.close()

    return candidates
