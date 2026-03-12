"""
Quora scanner — "Best books on X" questions reveal reader intent and gaps.
High-upvote answers recommending PD works = demand signal.
Questions about specific authors = intellectual interest signal.
"""
from playwright.sync_api import sync_playwright

SEARCH_QUERIES = [
    "best philosophical novels",
    "best classic literature must read",
    "thomas mann books",
    "kafka books read",
    "dostoevsky best book start",
    "books like nietzsche philosophy",
    "best annotated classics",
    "public domain philosophy books",
    "modernist literature best",
    "existentialist novels best",
    "books about bureaucracy alienation",
    "best 20th century european novels",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "camus": "Albert Camus",
    "rilke": "Rainer Maria Rilke", "musil": "Robert Musil",
}


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        page = ctx.new_page()

        for query in SEARCH_QUERIES:
            try:
                encoded = query.replace(" ", "%20")
                page.goto(f"https://www.quora.com/search?q={encoded}", timeout=20000)
                page.wait_for_timeout(3000)

                results = page.evaluate("""
                    () => Array.from(document.querySelectorAll('[class*="question"], .q-text, h2'))
                    .map(el => el.innerText.trim())
                    .filter(t => t.length > 10 && t.length < 300)
                    .slice(0, 20)
                """)

                for text in results:
                    text_lower = text.lower()
                    for kw, full_name in AUTHOR_KEYWORDS.items():
                        if kw in text_lower:
                            candidates.append({
                                "source": "quora",
                                "author": full_name,
                                "title": "",
                                "quora_question": text[:200],
                                "search_query": query,
                                "why_now": f"Quora reader intent: '{text[:80]}'",
                                "raw_score": 25,
                            })
                            break
            except Exception as e:
                print(f"  [quora/{query[:30]}] {e}")

        ctx.close()
        browser.close()

    return candidates
