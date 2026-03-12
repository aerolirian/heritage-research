"""
Substack scanner — literary newsletters and their reader engagement.
Target publications: The Honest Broker, The Marginalian, The Paris Review Notes,
Literary Kitchen, The Critic, Hudson Review, and high-traffic book/philosophy newsletters.
A Substack essay about a PD author = engaged intellectual readership paying attention.
"""
from playwright.sync_api import sync_playwright

# High-traffic literary/philosophical Substacks to monitor
TARGET_PUBLICATIONS = [
    ("https://tedgioia.substack.com", "The Honest Broker"),       # 250k+ subs, books/music/culture
    ("https://lithub.substack.com", "Literary Hub"),
    ("https://theparisreview.substack.com", "The Paris Review"),
    ("https://erikhoel.substack.com", "The Intrinsic Perspective"),  # philosophy/culture
    ("https://freddiedeboer.substack.com", "Freddie deBoer"),        # literary criticism
    ("https://samkriss.substack.com", "Sam Kriss"),                  # philosophical essays
    ("https://josephheath.substack.com", "In Due Course"),           # philosophy
    ("https://astralcodexten.substack.com", "Astral Codex Ten"),     # rationalist/philosophy
]

SEARCH_URL = "https://substack.com/search?q={query}&type=post"

SEARCH_QUERIES = [
    "Thomas Mann", "Franz Kafka", "Knut Hamsun", "James Joyce",
    "Dostoevsky", "Tolstoy", "Virginia Woolf", "Sinclair Lewis",
    "classic literature philosophy", "annotated edition",
    "public domain novel", "modernist literature",
]

AUTHOR_KEYWORDS = [
    "Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy", "Hamsun",
    "Hemingway", "Fitzgerald", "Woolf", "Lewis", "Conrad", "Flaubert",
]


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

        # Search Substack for author/topic posts
        for query in SEARCH_QUERIES:
            try:
                encoded = query.replace(" ", "%20")
                page.goto(SEARCH_URL.format(query=encoded), timeout=20000)
                page.wait_for_timeout(3000)

                posts = page.evaluate("""
                    () => Array.from(document.querySelectorAll('.post-preview, article, [class*="post"]'))
                    .slice(0, 15)
                    .map(el => ({
                        title: (el.querySelector('h2, h3, .post-title') || {}).innerText || '',
                        pub: (el.querySelector('.publication-name, .pub-name') || {}).innerText || '',
                        likes: (el.querySelector('.like-count, .reactions') || {}).innerText || '',
                        url: (el.querySelector('a[href*="/p/"]') || {}).href || '',
                    }))
                    .filter(p => p.title.length > 5)
                """)

                for post in posts:
                    title = post.get("title", "")
                    pub = post.get("pub", "")
                    likes = post.get("likes", "")
                    candidates.append({
                        "source": "substack",
                        "author": _extract_author(title + " " + query),
                        "title": "",
                        "substack_title": title,
                        "substack_pub": pub,
                        "substack_likes": likes,
                        "substack_url": post.get("url", ""),
                        "search_query": query,
                        "why_now": f"Substack essay: '{title[:70]}' ({pub}, {likes} likes)",
                        "raw_score": 35,
                    })
            except Exception as e:
                print(f"  [substack/{query}] {e}")

        browser.close()

    return candidates


AUTHOR_MAP = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
}


def _extract_author(text):
    t = text.lower()
    for k, v in AUTHOR_MAP.items():
        if k in t:
            return v
    return ""
