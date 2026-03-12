"""
Reddit scanner — monitors 30 literary/philosophical subreddits for PD title signals.
Uses PRAW read-only access. Never writes to Reddit, never stores user data.
"""
import praw
from collections import defaultdict
from datetime import datetime, timezone

SUBREDDITS = [
    # Title & author discovery
    "books", "literature", "classicbooks", "suggestmeabook",
    "booksuggestions", "52book", "WhatShouldIRead",
    # Contemporary hook angles
    "CriticalTheory", "philosophy", "geopolitics", "europe",
    "collapse", "changemyview", "NeutralPolitics", "HistoryofIdeas",
    # Philosophical intro material
    "continental", "AskPhilosophy", "literarytheory",
    "AskLiteraryStudies", "slatestarcodex", "Nietzsche",
    # Film & adaptation tracking
    "movies", "TrueFilm", "flicks", "Criterion",
    # Genre-specific
    "horrorlit", "Fantasy", "printSF", "historybooks", "bookclub",
]

# Public domain authors to track (death year <= 1954 for life+70 territories)
TRACKED_AUTHORS = [
    "Thomas Mann", "Sinclair Lewis", "Knut Hamsun", "James Joyce",
    "Virginia Woolf", "Franz Kafka", "Joseph Conrad", "Edith Wharton",
    "Theodore Dreiser", "Upton Sinclair", "Jack London", "O. Henry",
    "Willa Cather", "Sherwood Anderson", "F. Scott Fitzgerald",
    "Ernest Hemingway", "William Faulkner", "John Steinbeck",
    "Mikhail Bulgakov", "Fyodor Dostoevsky", "Leo Tolstoy",
    "Anton Chekhov", "Ivan Turgenev", "Gustave Flaubert", "Emile Zola",
    "Victor Hugo", "Alexandre Dumas", "Honore de Balzac",
    "Thomas Hardy", "George Eliot", "Charles Dickens",
]


def scan(config):
    reddit = praw.Reddit(
        client_id=config["reddit_client_id"],
        client_secret=config["reddit_client_secret"],
        user_agent=config["reddit_user_agent"],
        read_only=True,
    )

    mention_counts = defaultdict(lambda: {"count": 0, "posts": [], "subreddits": set()})

    for sub_name in SUBREDDITS:
        try:
            sub = reddit.subreddit(sub_name)
            for post in sub.hot(limit=100):
                text = f"{post.title} {post.selftext}".lower()
                for author in TRACKED_AUTHORS:
                    if author.lower() in text or author.split()[-1].lower() in text:
                        key = author
                        mention_counts[key]["count"] += 1
                        mention_counts[key]["subreddits"].add(sub_name)
                        if len(mention_counts[key]["posts"]) < 3:
                            mention_counts[key]["posts"].append({
                                "title": post.title,
                                "url": f"https://reddit.com{post.permalink}",
                                "score": post.score,
                                "subreddit": sub_name,
                            })
        except Exception as e:
            print(f"  [reddit/{sub_name}] {e}")

    candidates = []
    for author, data in mention_counts.items():
        if data["count"] >= 2:
            candidates.append({
                "source": "reddit",
                "author": author,
                "title": "",  # filled by scoring layer from known catalog
                "why_now": f"Mentioned {data['count']}x across {len(data['subreddits'])} subreddits",
                "subreddits": list(data["subreddits"]),
                "sample_posts": data["posts"],
                "raw_score": data["count"],
            })

    return candidates
