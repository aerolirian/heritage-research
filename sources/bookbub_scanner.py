"""
BookBub scanner — 15M+ readers, editorial picks signal commercial literary demand.
Featured deals on annotated/philosophical classics = what editors think will sell.
Also: BookBub lists and author follow counts signal reader investment in specific authors.
"""
from playwright.sync_api import sync_playwright

PAGES = [
    ("https://www.bookbub.com/books?category=literary+fiction&sort=featured", "literary_featured"),
    ("https://www.bookbub.com/books?category=classics&sort=featured", "classics_featured"),
    ("https://www.bookbub.com/books?category=literary+fiction&sort=new_release", "literary_new"),
    ("https://www.bookbub.com/lists/best-classic-literature", "best_classics_list"),
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

        for url, section in PAGES:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_timeout(3000)

                books = page.evaluate("""
                    () => Array.from(document.querySelectorAll('[class*="book"], article'))
                    .slice(0, 40)
                    .map(el => ({
                        title: (el.querySelector('[class*="title"], h3, h2') || {}).innerText || '',
                        author: (el.querySelector('[class*="author"]') || {}).innerText || '',
                        price: (el.querySelector('[class*="price"]') || {}).innerText || '',
                        rating: (el.querySelector('[class*="rating"], [class*="star"]') || {}).innerText || '',
                    }))
                    .filter(b => b.title.length > 3)
                """)

                for book in books:
                    title = book.get("title", "")
                    author = book.get("author", "")
                    if any(kw.lower() in author.lower() or kw.lower() in title.lower()
                           for kw in AUTHOR_KEYWORDS):
                        candidates.append({
                            "source": "bookbub",
                            "author": author,
                            "title": title,
                            "bookbub_section": section,
                            "bookbub_price": book.get("price", ""),
                            "bookbub_rating": book.get("rating", ""),
                            "why_now": f"BookBub {section}: '{title[:60]}' at {book.get('price','')}",
                            "raw_score": 35,
                        })
            except Exception as e:
                print(f"  [bookbub/{section}] {e}")

        browser.close()

    return candidates
