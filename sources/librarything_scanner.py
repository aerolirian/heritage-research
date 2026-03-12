"""
LibraryThing scanner — serious literary readers and catalogers.
More academic and literary than Goodreads. Strong signal for canonical/philosophical works.
Scrapes public lists and author pages via Playwright.
"""
from playwright.sync_api import sync_playwright

LISTS = [
    ("https://www.librarything.com/list/11765/all/Most-Read-Classic-Literature", "most_read_classics"),
    ("https://www.librarything.com/list/7395/all/Philosophical-Novels", "philosophical"),
    ("https://www.librarything.com/list/23/all/Best-Books-of-the-20th-Century", "20th_century"),
    ("https://www.librarything.com/list/4085/all/Literary-Fiction-at-its-finest", "literary_fiction"),
]

AUTHOR_KEYWORDS = [
    "Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy", "Hamsun",
    "Hemingway", "Fitzgerald", "Woolf", "Lewis", "Conrad", "Flaubert",
    "Chekhov", "Zola", "Hardy", "Dickens", "Hugo", "Balzac",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

        for url, list_name in LISTS:
            try:
                page.goto(url, timeout=20000)
                page.wait_for_timeout(2000)

                rows = page.evaluate("""
                    () => Array.from(document.querySelectorAll('.list_book, tr.list-item, .bookRecord'))
                    .slice(0, 100)
                    .map((el, i) => ({
                        rank: i + 1,
                        title: (el.querySelector('.title, a[href*="/work/"]') || {}).innerText || '',
                        author: (el.querySelector('.author, .authorName') || {}).innerText || '',
                        members: (el.querySelector('.members, .membercount') || {}).innerText || '',
                    }))
                    .filter(r => r.title.length > 2)
                """)

                for row in rows:
                    author = row.get("author", "")
                    title = row.get("title", "")
                    if any(kw.lower() in author.lower() or kw.lower() in title.lower()
                           for kw in AUTHOR_KEYWORDS):
                        candidates.append({
                            "source": "librarything",
                            "author": author,
                            "title": title,
                            "list": list_name,
                            "list_rank": row.get("rank", 0),
                            "members": row.get("members", ""),
                            "why_now": f"LibraryThing '{list_name}' list rank #{row.get('rank',0)} — {row.get('members','')} members",
                            "raw_score": max(10, 50 - row.get("rank", 50) * 0.4),
                        })
            except Exception as e:
                print(f"  [librarything/{list_name}] {e}")

        browser.close()

    return candidates
