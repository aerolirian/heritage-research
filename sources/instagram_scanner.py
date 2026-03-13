"""
Instagram scanner — which PD/annotated editions are getting traction,
what cover aesthetics perform, Heritage Canon aesthetic vs competitors.

Uses instaloader (github.com/instaloader/instaloader) — 11,900 stars, actively
maintained. Works anonymously for public hashtag data but is rate-limited.
For best results: provide a burner account session (not your real account).

Setup for session:
    instaloader --login=<burner_username>
    # saves session to ~/.config/instaloader/session-<username>
    # then set instagram_username in config
"""
import instaloader
from datetime import date, timedelta

HASHTAGS = [
    "booktok",
    "classicbooks",
    "annotatedbooks",
    "philosophicalfiction",
    "literarybooks",
    "bookstagram",
    "classiclit",
    "canonbooks",
    "greatliterature",
    "philosophybooks",
]

AUTHOR_KEYWORDS = {
    "mann": "Thomas Mann", "kafka": "Franz Kafka", "joyce": "James Joyce",
    "dostoevsky": "Fyodor Dostoevsky", "tolstoy": "Leo Tolstoy",
    "hamsun": "Knut Hamsun", "hemingway": "Ernest Hemingway",
    "fitzgerald": "F. Scott Fitzgerald", "woolf": "Virginia Woolf",
    "lewis": "Sinclair Lewis", "flaubert": "Gustave Flaubert",
    "chekhov": "Anton Chekhov", "nietzsche": "Friedrich Nietzsche",
}

POSTS_PER_TAG = 20
CUTOFF_DAYS = 90


def scan(config):
    candidates = []
    cutoff = date.today() - timedelta(days=CUTOFF_DAYS)

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
        max_connection_attempts=1,  # don't retry on 429/403
    )

    # Load session if available (burner account)
    username = config.get("instagram_username", "")
    if username:
        try:
            L.load_session_from_file(username)
        except Exception:
            pass  # fall back to anonymous

    for tag in HASHTAGS:
        count = 0
        try:
            hashtag = instaloader.Hashtag.from_name(L.context, tag)
            for post in hashtag.get_posts():
                if count >= POSTS_PER_TAG:
                    break
                if post.date.date() < cutoff:
                    break

                caption = (post.caption or "").lower()
                for kw, full_name in AUTHOR_KEYWORDS.items():
                    if kw in caption:
                        candidates.append({
                            "source": "instagram",
                            "author": full_name,
                            "title": "",
                            "hashtag": tag,
                            "ig_likes": post.likes,
                            "ig_comments": post.comments,
                            "ig_date": str(post.date.date()),
                            "ig_url": f"https://www.instagram.com/p/{post.shortcode}/",
                            "why_now": f"Instagram #{tag}: {post.likes:,} likes — '{caption[:60]}'",
                            "raw_score": min(60, 15 + post.likes / 1000),
                        })
                        break
                count += 1
        except Exception as e:
            print(f"  [instagram/#{tag}] {e}")

    return candidates
