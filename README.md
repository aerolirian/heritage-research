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

| Source | Signal | Auth |
|--------|--------|------|
| Reddit (PRAW) | Discussion velocity, contemporary angles | API key (see below) |
| Hacker News API | Intellectual discourse, book threads | None |
| Google Trends (pytrends) | Search momentum | None |
| Gutenberg download rankings | Sustained PD demand | None |
| TMDB | Upcoming film/TV adaptations | API key |
| OMDB | Existing adaptation sentiment | API key |
| Brave Search API | News, op-eds, speeches referencing authors | API key |
| Amazon (Playwright) | Competitor editions, BSR gaps | None |
| BookTok/Goodreads (Playwright) | Social traction, cover aesthetics | None |

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
