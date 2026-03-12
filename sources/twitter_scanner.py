"""
Twitter/X scanner — discourse around specific PD authors, trending philosophical
topics, viral essay threads. Scrapes public search via Playwright (API costs money).
"""
from playwright.sync_api import sync_playwright

SEARCH_QUERIES = [
    "Thomas Mann relevance",
    "Kafka bureaucracy",
    "Dostoevsky modern",
    "Hamsun nature",
    "classic literature annotated edition",
    "public domain philosophy novel",
    "great american novel 2025",
    "literary philosophy twitter",
]

AUTHOR_KEYWORDS = [
    ("Mann", "Thomas Mann"),
    ("Kafka", "Franz Kafka"),
    ("Joyce", "James Joyce"),
    ("Dostoevsky", "Fyodor Dostoevsky"),
    ("Tolstoy", "Leo Tolstoy"),
    ("Hamsun", "Knut Hamsun"),
    ("Hemingway", "Ernest Hemingway"),
    ("Fitzgerald", "F. Scott Fitzgerald"),
    ("Woolf", "Virginia Woolf"),
    ("Conrad", "Joseph Conrad"),
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = ctx.new_page()

        for query in SEARCH_QUERIES:
            try:
                encoded = query.replace(" ", "%20")
                page.goto(f"https://x.com/search?q={encoded}&f=live", timeout=20000)
                page.wait_for_timeout(4000)

                tweets = page.evaluate("""
                    () => Array.from(document.querySelectorAll('[data-testid="tweetText"]'))
                         .map(el => el.innerText)
                         .filter(t => t.length > 20)
                         .slice(0, 20)
                """)

                for tweet in tweets:
                    tweet_lower = tweet.lower()
                    for keyword, full_name in AUTHOR_KEYWORDS:
                        if keyword.lower() in tweet_lower:
                            candidates.append({
                                "source": "twitter",
                                "author": full_name,
                                "title": "",
                                "search_query": query,
                                "tweet": tweet[:280],
                                "why_now": f"Twitter discourse: '{tweet[:80].strip()}'",
                                "raw_score": 30,
                            })
                            break
            except Exception as e:
                print(f"  [twitter/{query[:30]}] {e}")

        ctx.close()
        browser.close()

    return candidates
