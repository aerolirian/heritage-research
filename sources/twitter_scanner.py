"""
Twitter/X scanner — discourse around PD authors, trending philosophical topics,
viral essay threads.

Uses twscrape (github.com/vladkens/twscrape) — 2,300 stars, actively maintained.
Uses X's internal GraphQL API (same as the web app). Requires real X accounts
for authentication — supports account rotation when rate-limited.

Setup:
    Add x_accounts to config as a list of {username, password, email, email_password}
    twscrape will manage sessions automatically.

Note: snscrape (the old go-to) has been dead since June 2023. twscrape is the
current standard for free X scraping.
"""
import asyncio
import twscrape

SEARCH_QUERIES = [
    "Thomas Mann book",
    "Franz Kafka relevance",
    "Dostoevsky modern",
    "Knut Hamsun",
    "classic literature annotated",
    "philosophy novel",
    "public domain philosophical edition",
    "great american novel 2025",
    "literary fiction",
    "Virginia Woolf stream consciousness",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "nietzsche": "Friedrich Nietzsche", "camus": "Albert Camus",
}

TWEETS_PER_QUERY = 20


async def _scan_async(config):
    candidates = []
    accounts = config.get("x_accounts", [])

    api = twscrape.API()

    # Add accounts if configured
    for acc in accounts:
        try:
            await api.pool.add_account(
                username=acc["username"],
                password=acc["password"],
                email=acc["email"],
                email_password=acc.get("email_password", ""),
            )
        except Exception as e:
            print(f"  [twitter/account] {e}")

    if accounts:
        try:
            await api.pool.login_all()
        except Exception as e:
            print(f"  [twitter/login] {e}")

    for query in SEARCH_QUERIES:
        count = 0
        try:
            async for tweet in api.search(query, limit=TWEETS_PER_QUERY):
                text = tweet.rawContent.lower()
                likes = tweet.likeCount
                retweets = tweet.retweetCount

                for kw, full_name in AUTHOR_KEYWORDS.items():
                    if kw in text:
                        candidates.append({
                            "source": "twitter",
                            "author": full_name,
                            "title": "",
                            "tweet_text": tweet.rawContent[:280],
                            "tweet_likes": likes,
                            "tweet_retweets": retweets,
                            "tweet_url": f"https://x.com/i/web/status/{tweet.id}",
                            "search_query": query,
                            "why_now": f"X/Twitter: {likes:,} likes — '{tweet.rawContent[:70]}'",
                            "raw_score": min(50, 15 + likes / 500 + retweets / 100),
                        })
                        break
                count += 1
                if count >= TWEETS_PER_QUERY:
                    break
        except Exception as e:
            print(f"  [twitter/{query[:30]}] {e}")

    return candidates


def scan(config):
    try:
        return asyncio.run(_scan_async(config))
    except Exception as e:
        print(f"  [twitter] {e}")
        return []
