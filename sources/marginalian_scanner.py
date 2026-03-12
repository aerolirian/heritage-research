"""
The Marginalian (formerly Brain Pickings) scanner — Maria Popova's philosophical
essay readership. One of the most-read literary/philosophy blogs on the internet.
Marginalian readers = Heritage Canon demographic almost by definition.
A recent Marginalian essay on a PD author = signal that audience is primed.
"""
from playwright.sync_api import sync_playwright

BASE = "https://www.themarginalian.org"

PAGES = [
    f"{BASE}/",
    f"{BASE}/category/books/",
    f"{BASE}/category/philosophy/",
    f"{BASE}/category/literature/",
]

AUTHOR_KEYWORDS = [
    "Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy", "Hamsun",
    "Hemingway", "Fitzgerald", "Woolf", "Conrad", "Flaubert",
    "Chekhov", "Rilke", "Nietzsche", "Camus", "Kierkegaard",
    "Schopenhauer", "Simone Weil", "Hannah Arendt",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

        for url in PAGES:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_timeout(2000)

                articles = page.evaluate("""
                    () => Array.from(document.querySelectorAll('h1 a, h2 a, h3 a, article a'))
                    .map(el => ({ title: el.innerText.trim(), url: el.href }))
                    .filter(a => a.title.length > 15 && a.url.includes('themarginalian'))
                    .slice(0, 40)
                """)

                for article in articles:
                    title = article.get("title", "")
                    matched = [kw for kw in AUTHOR_KEYWORDS if kw.lower() in title.lower()]
                    if matched:
                        candidates.append({
                            "source": "marginalian",
                            "author": matched[0],
                            "title": "",
                            "marginalian_title": title,
                            "marginalian_url": article.get("url", ""),
                            "why_now": f"The Marginalian: '{title[:80]}' — HC demographic primed",
                            "raw_score": 50,
                        })
            except Exception as e:
                print(f"  [marginalian/{url}] {e}")

        browser.close()

    return candidates
