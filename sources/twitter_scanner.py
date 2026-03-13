"""
Twitter/X scanner — discourse around PD authors, trending philosophical topics,
viral essay threads.

Uses Playwright via a residential SOCKS5 proxy (home PC tunnel on localhost:1081).
The tunnel is created by running on the home PC:
    ssh -D 1080 -R 1081:localhost:1080 -N ubuntu@130.61.87.230

Falls back to twscrape if the proxy is not available.

Loads session cookies from x.com_cookies.txt in GDrive root.
"""
import json
import socket
from pathlib import Path

SEARCH_QUERIES = [
    "Thomas Mann book",
    "Franz Kafka relevance",
    "Sinclair Lewis America",
    "Knut Hamsun Growth of the Soil",
    "James Joyce Portrait Artist",
    "F. Scott Fitzgerald Gatsby",
    "classic literature philosophical edition",
    "public domain annotated novel",
    "Dostoevsky modern relevance",
    "Virginia Woolf consciousness",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "nietzsche": "Friedrich Nietzsche", "camus": "Albert Camus",
}

SOCKS_PROXY = "socks5://localhost:1081"
COOKIES_PATH = Path.home() / "gdrive" / "heritage_audiobooks" / "x.com_cookies.txt"


def _proxy_available():
    try:
        s = socket.create_connection(("localhost", 1081), timeout=2)
        s.close()
        return True
    except OSError:
        return False


def _load_cookies():
    if not COOKIES_PATH.exists():
        return []
    import http.cookiejar
    jar = http.cookiejar.MozillaCookieJar()
    jar.load(str(COOKIES_PATH), ignore_discard=True, ignore_expires=True)
    return [{"name": c.name, "value": c.value, "domain": c.domain,
             "path": c.path, "secure": bool(c.secure)} for c in jar]


def _scan_playwright(config):
    from playwright.sync_api import sync_playwright
    cookies = _load_cookies()
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": SOCKS_PROXY},
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        )
        if cookies:
            ctx.add_cookies(cookies)

        page = ctx.new_page()

        for query in SEARCH_QUERIES:
            try:
                url = f"https://x.com/search?q={query.replace(' ', '+')}&f=live"
                page.goto(url, timeout=20000)
                page.wait_for_timeout(3000)

                if "login" in page.url:
                    print("  [twitter] not logged in — cookies expired or missing")
                    break

                articles = page.query_selector_all('article[data-testid="tweet"]')
                for article in articles[:10]:
                    text_el = article.query_selector('[data-testid="tweetText"]')
                    likes_el = article.query_selector('[data-testid="like"]')
                    rts_el = article.query_selector('[data-testid="retweet"]')
                    if not text_el:
                        continue
                    text = text_el.inner_text()
                    text_lower = text.lower()
                    try:
                        likes = int(likes_el.inner_text().replace(",", "")) if likes_el and likes_el.inner_text().strip() else 0
                    except ValueError:
                        likes = 0
                    try:
                        rts = int(rts_el.inner_text().replace(",", "")) if rts_el and rts_el.inner_text().strip() else 0
                    except ValueError:
                        rts = 0

                    for kw, full_name in AUTHOR_KEYWORDS.items():
                        if kw in text_lower:
                            candidates.append({
                                "source": "twitter",
                                "author": full_name,
                                "title": "",
                                "tweet_text": text[:280],
                                "tweet_likes": likes,
                                "tweet_retweets": rts,
                                "search_query": query,
                                "why_now": f"X/Twitter: {likes:,} likes — '{text[:70]}'",
                                "raw_score": min(50, 15 + likes / 500 + rts / 100),
                            })
                            break
            except Exception as e:
                print(f"  [twitter/{query[:30]}] {e}")

        browser.close()

    return candidates


def _scan_twscrape(config):
    import asyncio
    import twscrape

    async def _async(config):
        candidates = []
        accounts = config.get("x_accounts", [])
        api = twscrape.API()
        for acc in accounts:
            try:
                await api.pool.add_account(
                    username=acc["username"], password=acc["password"],
                    email=acc["email"], email_password=acc.get("email_password", ""),
                )
            except Exception:
                pass
        if accounts:
            try:
                await api.pool.login_all()
            except Exception:
                pass
        for query in SEARCH_QUERIES:
            try:
                async for tweet in api.search(query, limit=20):
                    text = tweet.rawContent.lower()
                    for kw, full_name in AUTHOR_KEYWORDS.items():
                        if kw in text:
                            candidates.append({
                                "source": "twitter",
                                "author": full_name,
                                "title": "",
                                "tweet_text": tweet.rawContent[:280],
                                "tweet_likes": tweet.likeCount,
                                "tweet_retweets": tweet.retweetCount,
                                "search_query": query,
                                "why_now": f"X/Twitter: {tweet.likeCount:,} likes — '{tweet.rawContent[:70]}'",
                                "raw_score": min(50, 15 + tweet.likeCount / 500 + tweet.retweetCount / 100),
                            })
                            break
            except Exception as e:
                print(f"  [twitter/twscrape/{query[:30]}] {e}")
        return candidates

    return asyncio.run(_async(config))


def scan(config):
    try:
        if _proxy_available():
            print("  [twitter] using residential proxy (home PC tunnel)")
            return _scan_playwright(config)
        else:
            print("  [twitter] proxy not available — trying twscrape")
            return _scan_twscrape(config)
    except Exception as e:
        print(f"  [twitter] {e}")
        return []
