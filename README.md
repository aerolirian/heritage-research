# heritage-research

A research pipeline for identifying culturally relevant public domain literary works for philosophical annotated editions.

## What it does

Scans multiple public data sources weekly to surface PD title candidates, ranks them by cultural signal strength, and produces acquisition briefs for editorial review. Each candidate gets:

- **Author + title** — what to publish
- **PD status by territory** — copyright clearance summary
- **Why now** — the specific signal driving urgency (film adaptation, trend spike, political relevance, underserved market)
- **Subtitle angle** — a concrete contemporary hook
- **Intellectual brief** — 2–3 paragraphs: the argument the introduction should make, the philosophical tradition it sits in, key contemporary parallels

Target: 10–20 ranked candidates per weekly sweep.

## Data sources

| Source | Signal | Auth | Weight |
|--------|--------|------|--------|
| TMDB | Upcoming film/TV adaptations | API key | 80 |
| Anniversary calendar | Publication centennials — defined media window | None | 70 |
| Wikipedia pageviews | Author/title traffic spikes — something just happened | None | 65 |
| Reddit (PRAW) | Discussion velocity across 30 subreddits | API key | 50 |
| Google Trends (pytrends) | Search momentum spikes | None | 45 |
| Gutenberg download rankings | Sustained PD download demand | None | 40 |
| YouTube | Literary/philosophical video essays | API key (optional) | 40 |
| Goodreads (Playwright) | List rankings, annotated shelf traction | None | 35 |
| Hacker News API | Intellectual discourse, book threads | None | 35 |
| Letterboxd (Playwright) | Film-literary adaptation community | None | 35 |
| OpenSyllabus (Playwright) | University course teaching frequency | None | 35 |
| TikTok/BookTok (Playwright) | Organic social traction, angles | None | 30 |
| Brave Search API | News, op-eds, speeches referencing authors | API key | 30 |
| Instagram (Playwright) | Cover aesthetics, visual traction | None | 25 |
| Amazon (Playwright) | Competitor editions, BSR gaps | None | 25 |
| Twitter/X (Playwright) | Discourse, viral essay threads | None | 25 |
| OMDB | Existing adaptation sentiment | API key | — |
| The Marginalian (Playwright) | Maria Popova essays — HC demographic primed | None | 50 |
| Podcast RSS feeds | Episode-length author treatment — deep audience engagement | None | 45 |
| Literary Hub (Playwright) | Biggest literary publication — aggregates all serious coverage | None | 45 |
| Five Books (Playwright) | Expert curated lists — intellectual legitimacy + subtitle angles | None | 40 |
| LibraryThing (Playwright) | Serious literary catalogers — more academic than Goodreads | None | 38 |
| Substack (Playwright) | Literary newsletter reader engagement | None | 38 |
| Open Library API | Borrow counts + reading lists — actual PD reader demand | None | 35 |
| The StoryGraph (Playwright) | Goodreads alternative — mood/theme tags inform subtitle angles | None | 35 |
| Stack Exchange API | Close reading questions — deep engagement signal | None | 35 |
| BookBub (Playwright) | 15M readers — editorial picks signal commercial literary demand | None | 30 |
| Tumblr (Playwright) | Younger readers discovering European modernism | API key (opt.) | 28 |
| Quora (Playwright) | "Best books on X" intent signal — reveals gaps | None | 25 |

## Subreddits monitored

**Title & author discovery** (7): r/books, r/literature, r/classicbooks, r/suggestmeabook, r/booksuggestions, r/52book, r/WhatShouldIRead

**Contemporary hook angles** (8): r/CriticalTheory, r/philosophy, r/geopolitics, r/europe, r/collapse, r/changemyview, r/NeutralPolitics, r/HistoryofIdeas

**Philosophical intro material** (6): r/continental, r/AskPhilosophy, r/literarytheory, r/AskLiteraryStudies, r/slatestarcodex, r/Nietzsche

**Film & adaptation tracking** (4): r/movies, r/TrueFilm, r/flicks, r/Criterion

**Genre-specific** (5): r/horrorlit, r/Fantasy, r/printSF, r/historybooks, r/bookclub

Total: 30 subreddits

## Usage

```bash
# Weekly sweep — produces candidates.json + report.md
python research.py sweep

# Single-source run
python research.py sweep --source reddit
python research.py sweep --source tmdb
python research.py sweep --source gutenberg

# Show ranked candidates from last sweep
python research.py report

# Check PD status for a specific author
python research.py pd "Knut Hamsun" --death-year 1952
```

## Setup

```bash
pip install praw pytrends requests playwright lxml
playwright install chromium
cp config.example.json ~/.heritage_research.json
# fill in API keys
```

## Config (`~/.heritage_research.json`)

```json
{
  "reddit_client_id": "",
  "reddit_client_secret": "",
  "reddit_user_agent": "heritage-research/1.0 by aerolirian",
  "tmdb_api_key": "",
  "omdb_api_key": "",
  "brave_api_key": "",
  "openai_api_key": ""
}
```

### Getting API keys

**Reddit**: reddit.com/prefs/apps → create app → type: **script** → redirect URI: `http://localhost:8080`

**TMDB**: themoviedb.org/settings/api (free, instant approval)

**OMDB**: omdbapi.com/#apikey (free tier, email only)

**Brave**: api.search.brave.com (free tier: 2,000 queries/month)

## Architecture

```
research.py          ← CLI entry point
sources/
  reddit_scanner.py  ← PRAW-based subreddit monitoring
  hn_scanner.py      ← HN Algolia API
  gutenberg.py       ← Download ranking scraper
  tmdb_scanner.py    ← Upcoming adaptations via TMDB API
  trends.py          ← pytrends Google Trends
  brave_scanner.py   ← News/op-ed monitoring
  amazon_scanner.py  ← Playwright: competitor BSR analysis
scoring.py           ← Rank candidates by signal strength
copyright.py         ← PD status by territory (life+50/60/70/80/100)
brief.py             ← GPT-4.1-nano acquisition brief generator
output/              ← Weekly reports (candidates.json, report.md)
```

## How Reddit data is used

- Read-only access to **public** subreddit posts and comments via PRAW
- Tracks mention frequency of classic authors/titles week-over-week
- Extracts discussion themes (what contemporary angle readers connect to a given work)
- Monitors adaptation announcement threads
- Never writes to Reddit
- Never accesses private data
- Never stores usernames or personal information
- Only aggregates mention counts and discussion themes from public text

## Part of the Heritage Canon series

Heritage Canon publishes philosophical annotated editions of public domain literary works to major ebook platforms (Apple Books, Google Play Books, Kobo, Barnes & Noble Press). Each edition includes an original ~5,000-word philosophical introduction analysing the work's central arguments and contemporary relevance.

This research pipeline feeds the title acquisition side of that process.
