"""
The StoryGraph scanner — fastest-growing Goodreads alternative.
Younger, more literary audience. Mood/theme tagging gives richer signal
about WHY readers are drawn to specific works (e.g. "dark", "philosophical",
"slow-burn", "challenging") — useful for subtitle angle generation.
"""
from playwright.sync_api import sync_playwright

BROWSE_URLS = [
    ("https://app.thestorygraph.com/browse?genres=classics&sort_by=rating", "classics_rated"),
    ("https://app.thestorygraph.com/browse?genres=literary-fiction&sort_by=rating", "literary_rated"),
    ("https://app.thestorygraph.com/browse?genres=philosophy&sort_by=rating", "philosophy_rated"),
    ("https://app.thestorygraph.com/browse?genres=classics&sort_by=to_reads", "classics_wanted"),
]

AUTHOR_KEYWORDS = [
    "Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy", "Hamsun",
    "Hemingway", "Fitzgerald", "Woolf", "Lewis", "Conrad", "Flaubert",
    "Chekhov", "Zola", "Hardy", "Dickens", "Hugo",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

        for url, list_name in BROWSE_URLS:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_timeout(3000)

                results = page.evaluate("""
                    () => Array.from(document.querySelectorAll('.book-title-author-and-series, .book-pane'))
                    .slice(0, 50)
                    .map((el, i) => ({
                        rank: i + 1,
                        title: (el.querySelector('h3, .book-title') || {}).innerText || '',
                        author: (el.querySelector('.author-text, .authors') || {}).innerText || '',
                        rating: (el.querySelector('.average-star-rating, .rating') || {}).innerText || '',
                        moods: Array.from(el.querySelectorAll('.mood, .pace, .tag')).map(t => t.innerText).join(', '),
                    }))
                    .filter(r => r.title.length > 2)
                """)

                for r in results:
                    author = r.get("author", "")
                    title = r.get("title", "")
                    if any(kw.lower() in author.lower() or kw.lower() in title.lower()
                           for kw in AUTHOR_KEYWORDS):
                        candidates.append({
                            "source": "storygraph",
                            "author": author,
                            "title": title,
                            "list": list_name,
                            "list_rank": r.get("rank", 0),
                            "storygraph_rating": r.get("rating", ""),
                            "storygraph_moods": r.get("moods", ""),
                            "why_now": f"StoryGraph '{list_name}' rank #{r.get('rank',0)} — moods: {r.get('moods','')[:60]}",
                            "raw_score": max(10, 45 - r.get("rank", 45) * 0.5),
                        })
            except Exception as e:
                print(f"  [storygraph/{list_name}] {e}")

        browser.close()

    return candidates
