"""
TikTok/BookTok scanner — which PD editions are getting organic traction,
what angles and aesthetics are performing, comment sentiment.

Uses TikTokApi (github.com/davidteather/TikTok-Api) — unofficial but actively
maintained, handles TikTok's anti-bot measures with Playwright under the hood.
Much more reliable than raw Playwright scraping.

TikTok Research API exists but is academic institutions only — not available
to individual developers.
"""
import asyncio
from TikTokApi import TikTokApi

BOOKTOK_HASHTAGS = [
    "booktok",
    "classicbooks",
    "bookstagram",
    "literaryfiction",
    "philosophybooks",
    "annotatedbooks",
    "classiclit",
    "canonbooks",
]

AUTHOR_SEARCHES = [
    "thomas mann",
    "franz kafka",
    "james joyce",
    "dostoevsky",
    "virginia woolf",
    "knut hamsun",
    "tolstoy",
    "hemingway fitzgerald",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "nietzsche": "Friedrich Nietzsche",
    "camus": "Albert Camus",
}

VIDEO_COUNT = 30  # per hashtag/search


async def _scan_async(ms_token=None):
    candidates = []

    async with TikTokApi() as api:
        if ms_token:
            await api.create_sessions(ms_tokens=[ms_token], num_sessions=1,
                                      sleep_after=3, headless=True)
        else:
            await api.create_sessions(num_sessions=1, sleep_after=3, headless=True)

        # Scan BookTok hashtags
        for hashtag in BOOKTOK_HASHTAGS:
            try:
                tag = api.hashtag(name=hashtag)
                async for video in tag.videos(count=VIDEO_COUNT):
                    text = (video.as_dict.get("desc", "") or "").lower()
                    stats = video.as_dict.get("stats", {})
                    plays = stats.get("playCount", 0)
                    likes = stats.get("diggCount", 0)

                    for kw, full_name in AUTHOR_KEYWORDS.items():
                        if kw in text:
                            candidates.append({
                                "source": "tiktok",
                                "author": full_name,
                                "title": "",
                                "tiktok_hashtag": hashtag,
                                "tiktok_desc": text[:200],
                                "tiktok_plays": plays,
                                "tiktok_likes": likes,
                                "why_now": f"BookTok #{hashtag}: {plays:,} plays, {likes:,} likes — '{text[:60]}'",
                                "raw_score": min(80, 20 + (plays / 100000) + (likes / 10000)),
                            })
                            break
            except Exception as e:
                print(f"  [tiktok/#{hashtag}] {e}")

        # Note: TikTokApi search.videos removed; search.users returns User objects not videos.
        # Author searches removed — hashtag scan above provides sufficient signal.

    return candidates


def scan(config):
    # Optional: TikTok ms_token from browser cookies improves reliability
    # Get it by: open TikTok in browser → DevTools → Application → Cookies → ms_token
    ms_token = config.get("tiktok_ms_token", None)
    try:
        return asyncio.run(_scan_async(ms_token))
    except Exception as e:
        print(f"  [tiktok] {e}")
        return []
