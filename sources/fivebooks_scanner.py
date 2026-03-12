"""
Five Books scanner — expert curated reading lists (academics, writers, thinkers).
"Best books on existentialism", "Best novels about bureaucracy", etc.
Signal: what experts recommend = underserved titles with intellectual legitimacy.
Strong for subtitle angle generation — experts articulate exactly why a book matters.
"""
from playwright.sync_api import sync_playwright

CATEGORY_URLS = [
    ("https://fivebooks.com/category/philosophy/", "philosophy"),
    ("https://fivebooks.com/category/literature/", "literature"),
    ("https://fivebooks.com/category/history-of-ideas/", "history_of_ideas"),
    ("https://fivebooks.com/category/20th-century-history/", "20th_century"),
    ("https://fivebooks.com/best-books/classic-literature/", "classics"),
    ("https://fivebooks.com/best-books/philosophy-of-mind/", "philosophy_mind"),
]

AUTHOR_KEYWORDS = [
    "Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy", "Hamsun",
    "Hemingway", "Fitzgerald", "Woolf", "Lewis", "Conrad", "Flaubert",
    "Chekhov", "Zola", "Hardy", "Camus", "Sartre", "Nietzsche",
    "Rilke", "Musil", "Broch", "Svevo", "Schnitzler",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

        for url, category in CATEGORY_URLS:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_timeout(2000)

                items = page.evaluate("""
                    () => Array.from(document.querySelectorAll('.interview-item, article, .book-recommendation'))
                    .slice(0, 30)
                    .map(el => ({
                        title: (el.querySelector('h2, h3, .book-title') || {}).innerText || '',
                        author: (el.querySelector('.author, .book-author') || {}).innerText || '',
                        expert: (el.querySelector('.interviewer, .recommender') || {}).innerText || '',
                        url: (el.querySelector('a') || {}).href || '',
                    }))
                    .filter(r => r.title.length > 5)
                """)

                for item in items:
                    title = item.get("title", "")
                    author = item.get("author", "")
                    expert = item.get("expert", "")
                    matched = [kw for kw in AUTHOR_KEYWORDS
                               if kw.lower() in title.lower() or kw.lower() in author.lower()]
                    if matched:
                        candidates.append({
                            "source": "fivebooks",
                            "author": author or matched[0],
                            "title": title,
                            "fivebooks_category": category,
                            "fivebooks_expert": expert,
                            "fivebooks_url": item.get("url", ""),
                            "why_now": f"Expert-recommended on Five Books ({category}): recommended by {expert or 'expert'}",
                            "raw_score": 40,
                        })
            except Exception as e:
                print(f"  [fivebooks/{category}] {e}")

        browser.close()

    return candidates
