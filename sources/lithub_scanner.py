"""
Literary Hub scanner — biggest online literary publication.
Aggregates coverage from NYT, New Yorker, Guardian, Paris Review, etc.
What's trending on LitHub = what the entire serious literary readership is talking about.
Also scrapes: most-read lists, essay picks, book recommendations.
"""
from playwright.sync_api import sync_playwright

PAGES = [
    ("https://lithub.com/category/craft-and-criticism/", "criticism"),
    ("https://lithub.com/category/the-reading-life/", "reading_life"),
    ("https://lithub.com/most-read/", "most_read"),
    ("https://lithub.com/category/book-reviews/", "reviews"),
]

AUTHOR_KEYWORDS = [
    "Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy", "Hamsun",
    "Hemingway", "Fitzgerald", "Woolf", "Lewis", "Conrad", "Flaubert",
    "Chekhov", "Zola", "Hardy", "Dickens", "Hugo", "Balzac",
    "Nietzsche", "Camus", "Sartre", "Beckett", "Faulkner", "Steinbeck",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

        for url, section in PAGES:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_timeout(2000)

                articles = page.evaluate("""
                    () => Array.from(document.querySelectorAll('article, .post, h2 a, h3 a'))
                    .slice(0, 30)
                    .map(el => {
                        const a = el.tagName === 'A' ? el : el.querySelector('a');
                        return {
                            title: (el.querySelector('h2, h3, .entry-title') || el).innerText || '',
                            url: a ? a.href : '',
                        };
                    })
                    .filter(a => a.title.length > 10)
                """)

                for article in articles:
                    title = article.get("title", "")
                    matched = [kw for kw in AUTHOR_KEYWORDS if kw.lower() in title.lower()]
                    if matched:
                        candidates.append({
                            "source": "lithub",
                            "author": matched[0],
                            "title": "",
                            "lithub_title": title,
                            "lithub_section": section,
                            "lithub_url": article.get("url", ""),
                            "why_now": f"Literary Hub {section}: '{title[:80]}'",
                            "raw_score": 40,
                        })
            except Exception as e:
                print(f"  [lithub/{section}] {e}")

        browser.close()

    return candidates
