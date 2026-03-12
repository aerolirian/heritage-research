"""
The StoryGraph scanner — fastest-growing Goodreads alternative.
Mood/theme tagging ("dark", "philosophical", "slow-burn", "challenging") gives
richer signal about WHY readers are drawn to specific works — useful for subtitle angles.

Uses storygraph-api (github.com/ym496/storygraph-api) — Python scraper wrapper.
Requires a StoryGraph account for full data.
Falls back to Playwright for public browse pages if no credentials.
"""
from storygraph_api import StoryGraph

SEARCH_TITLES = [
    "Buddenbrooks", "The Trial", "Growth of the Soil", "Ulysses",
    "The Great Gatsby", "Crime and Punishment", "Anna Karenina",
    "Madame Bovary", "Mrs Dalloway", "The Sun Also Rises",
    "Death in Venice", "A Portrait of the Artist as a Young Man",
    "Heart of Darkness", "The Picture of Dorian Gray",
    "Wuthering Heights", "The Sound and the Fury",
]

AUTHOR_MAP = {
    "buddenbrooks": "Thomas Mann",
    "the trial": "Franz Kafka",
    "growth of the soil": "Knut Hamsun",
    "ulysses": "James Joyce",
    "the great gatsby": "F. Scott Fitzgerald",
    "crime and punishment": "Fyodor Dostoevsky",
    "anna karenina": "Leo Tolstoy",
    "madame bovary": "Gustave Flaubert",
    "mrs dalloway": "Virginia Woolf",
    "the sun also rises": "Ernest Hemingway",
    "death in venice": "Thomas Mann",
    "a portrait of the artist as a young man": "James Joyce",
    "heart of darkness": "Joseph Conrad",
    "the picture of dorian gray": "Oscar Wilde",
    "wuthering heights": "Emily Brontë",
    "the sound and the fury": "William Faulkner",
}


def scan(config):
    candidates = []
    username = config.get("storygraph_username", "")
    password = config.get("storygraph_password", "")

    if not username or not password:
        print("  [storygraph] no credentials — skipping (add storygraph_username + storygraph_password to config)")
        return _scan_playwright()

    try:
        sg = StoryGraph(username, password)

        for title in SEARCH_TITLES:
            try:
                results = sg.search_books(title)
                if not results:
                    continue
                book = results[0]
                author = AUTHOR_MAP.get(title.lower(), "")
                moods = ", ".join(book.get("moods", [])[:5])
                pace = book.get("pace", "")
                rating = book.get("average_rating", "")
                ratings_count = book.get("ratings_count", 0)

                candidates.append({
                    "source": "storygraph",
                    "author": author,
                    "title": title,
                    "storygraph_rating": rating,
                    "storygraph_ratings": ratings_count,
                    "storygraph_moods": moods,
                    "storygraph_pace": pace,
                    "why_now": f"StoryGraph: {rating}/5 ({ratings_count} ratings) — moods: {moods}",
                    "raw_score": 30 + (float(rating) * 2 if rating else 0),
                })
            except Exception as e:
                print(f"  [storygraph/{title}] {e}")

    except Exception as e:
        print(f"  [storygraph/login] {e}")

    return candidates


def _scan_playwright():
    """Playwright fallback for public browse pages (no login)."""
    from playwright.sync_api import sync_playwright
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for title in SEARCH_TITLES[:8]:
            try:
                encoded = title.replace(" ", "+")
                page.goto(f"https://app.thestorygraph.com/search?q={encoded}", timeout=20000)
                page.wait_for_timeout(3000)
                result = page.evaluate("""
                    () => {
                        const el = document.querySelector('.book-pane, .book-title-author-and-series');
                        return el ? { text: el.innerText } : null;
                    }
                """)
                if result:
                    author = AUTHOR_MAP.get(title.lower(), "")
                    candidates.append({
                        "source": "storygraph",
                        "author": author,
                        "title": title,
                        "why_now": f"StoryGraph: '{title}' in search results",
                        "raw_score": 25,
                    })
            except Exception as e:
                print(f"  [storygraph_playwright/{title}] {e}")

        browser.close()

    return candidates
