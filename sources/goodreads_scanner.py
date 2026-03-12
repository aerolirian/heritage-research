"""
Goodreads scanner — uses Playwright to scrape public lists and shelves.
Signals: organic traction on specific PD titles, reader-driven "want to read" momentum,
which philosophical/annotated editions are performing, cover aesthetic trends.
"""
from playwright.sync_api import sync_playwright

# Public Goodreads lists likely to surface high-signal PD candidates
LISTS = [
    # Listopia
    ("https://www.goodreads.com/list/show/264.Best_Books_Ever", "best_ever"),
    ("https://www.goodreads.com/list/show/1.Best_Books_of_the_20th_Century", "20th_century"),
    ("https://www.goodreads.com/list/show/478.Philosophical_Novels", "philosophical"),
    ("https://www.goodreads.com/list/show/3.Best_Classic_Literature", "classics"),
    ("https://www.goodreads.com/list/show/511.Books_That_Should_Be_Made_Into_Movies_Or_TV_series", "adaptation_wishlist"),
    ("https://www.goodreads.com/list/show/12719.Books_Every_Intellectual_Should_Read", "intellectual"),
]

# Specific shelves for annotated/philosophical editions (competitor analysis)
SHELVES = [
    "https://www.goodreads.com/shelf/show/annotated-classics",
    "https://www.goodreads.com/shelf/show/philosophical-fiction",
    "https://www.goodreads.com/shelf/show/literary-classics",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

        # Scan Listopia lists
        for url, list_name in LISTS:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_selector("tr.bookalike", timeout=8000)
                rows = page.query_selector_all("tr.bookalike")
                for rank, row in enumerate(rows[:50], 1):
                    title_el = row.query_selector("td.title a")
                    author_el = row.query_selector("td.author a")
                    votes_el = row.query_selector("td.score")
                    if not title_el:
                        continue
                    title = title_el.inner_text().strip()
                    author = author_el.inner_text().strip() if author_el else ""
                    votes = votes_el.inner_text().strip() if votes_el else ""
                    candidates.append({
                        "source": "goodreads",
                        "title": title,
                        "author": author,
                        "list": list_name,
                        "list_rank": rank,
                        "votes": votes,
                        "why_now": f"Rank #{rank} on Goodreads '{list_name}' list ({votes} votes)",
                        "raw_score": max(0, 50 - rank),
                    })
            except Exception as e:
                print(f"  [goodreads/{list_name}] {e}")

        # Scan competitor annotated edition shelves
        for url in SHELVES:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_selector(".bookTitle", timeout=8000)
                books = page.query_selector_all(".bookTitle")
                authors = page.query_selector_all(".authorName")
                for i, (book_el, author_el) in enumerate(zip(books[:30], authors)):
                    title = book_el.inner_text().strip()
                    author = author_el.inner_text().strip() if author_el else ""
                    candidates.append({
                        "source": "goodreads",
                        "title": title,
                        "author": author,
                        "list": "annotated_shelf",
                        "list_rank": i + 1,
                        "why_now": f"On Goodreads annotated/philosophical shelf (rank #{i+1})",
                        "raw_score": 20,
                    })
            except Exception as e:
                print(f"  [goodreads/shelf] {e}")

        browser.close()

    return candidates
