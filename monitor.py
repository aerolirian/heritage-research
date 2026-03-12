#!/usr/bin/env python3
"""
monitor.py — Daily spike monitor for published Heritage Canon books.

Runs fast sources only (Wikipedia, Reddit, TMDB, Anniversary) — no Playwright.
Designed to run daily via cron. Sends email or prints alert when a promotion
window opens for an already-published book.

Cron (daily at 8am):
    0 8 * * * cd /home/ubuntu/heritage-research && ~/miniconda3/envs/nemo_tn/bin/python3 monitor.py >> /tmp/heritage_monitor.log 2>&1

Usage:
    python monitor.py                   # check all signals, print alerts
    python monitor.py --email           # also send alert email
    python monitor.py --promote         # auto-run promote.py if alerts found
"""
import argparse
import json
import smtplib
import subprocess
import sys
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

CONFIG_PATH = Path.home() / ".heritage_research.json"


def load_config():
    if not CONFIG_PATH.exists():
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


PUBLISHED_AUTHORS = {
    "lewis": "Arrowsmith (Sinclair Lewis)",
    "fitzgerald": "The Great Gatsby (F. Scott Fitzgerald)",
    "mann": "Buddenbrooks (Thomas Mann)",
    "hamsun": "Growth of the Soil (Knut Hamsun)",
    "joyce": "A Portrait of the Artist (James Joyce)",
}


def run_fast_sources(config):
    """Run only the fast, no-Playwright sources."""
    candidates = []
    for source in ["wikipedia", "tmdb", "anniversary", "reddit", "hn"]:
        try:
            if source == "wikipedia":
                from sources.wikipedia_scanner import scan
            elif source == "tmdb":
                from sources.tmdb_scanner import scan
            elif source == "anniversary":
                from sources.anniversary_scanner import scan
            elif source == "reddit":
                from sources.reddit_scanner import scan
            elif source == "hn":
                from sources.hn_scanner import scan
            results = scan(config)
            candidates.extend(results)
            print(f"  [{source}] {len(results)} signals")
        except Exception as e:
            print(f"  [{source}] {e}")
    return candidates


def find_alerts(candidates):
    alerts = []

    for c in candidates:
        author_last = (c.get("author", "").split()[-1] or "").lower()
        book = PUBLISHED_AUTHORS.get(author_last)
        if not book:
            continue

        source = c.get("source", "")

        if source == "wikipedia":
            ratio = c.get("wiki_spike_ratio", 1)
            if ratio >= 1.5:
                alerts.append({
                    "urgency": "HIGH" if ratio >= 2.0 else "MEDIUM",
                    "type": "Wikipedia spike",
                    "book": book,
                    "detail": f"{ratio}x above 90-day average ({c.get('wiki_recent_daily', 0):,} views/day)",
                    "action": "Post on Reddit + email list today. 48-hour window.",
                })

        elif source == "tmdb":
            rel = c.get("release_date", "")
            try:
                from datetime import date as d
                rel_date = d.fromisoformat(rel)
                days = (rel_date - d.today()).days
                if -7 <= days <= 90:
                    alerts.append({
                        "urgency": "HIGH" if days <= 14 else "MEDIUM",
                        "type": "Film adaptation",
                        "book": book,
                        "detail": f"'{c.get('adaptation_title','')}' releases {rel} ({days}d away)",
                        "action": "Push on Letterboxd, r/movies, r/TrueFilm, r/books now.",
                    })
            except Exception:
                pass

        elif source == "anniversary":
            years = c.get("years_away", 99)
            if abs(years) <= 1:
                alerts.append({
                    "urgency": "HIGH" if years == 0 else "MEDIUM",
                    "type": "Centennial",
                    "book": book,
                    "detail": f"Publication centennial {c.get('centennial_year')} ({years:+d}y)",
                    "action": "Pitch Literary Hub, Marginalian, email list, Reddit this week.",
                })

        elif source == "reddit" and c.get("raw_score", 0) >= 8:
            alerts.append({
                "urgency": "LOW",
                "type": "Reddit momentum",
                "book": book,
                "detail": f"Mentioned {c.get('raw_score',0)}x in {', '.join(c.get('subreddits',[])[:3])}",
                "action": "Join conversation organically in active threads.",
            })

    return alerts


def format_alerts(alerts):
    if not alerts:
        return f"[{date.today()}] No promotion alerts today.\n"

    lines = [f"HERITAGE CANON PROMOTION ALERTS — {date.today()}", "=" * 50]
    for a in sorted(alerts, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["urgency"]]):
        lines.append(f"\n[{a['urgency']}] {a['type']} — {a['book']}")
        lines.append(f"  Detail: {a['detail']}")
        lines.append(f"  Action: {a['action']}")
    return "\n".join(lines)


def send_email(text, config):
    smtp_user = config.get("alert_email_from", "")
    smtp_pass = config.get("alert_email_password", "")
    smtp_to = config.get("alert_email_to", smtp_user)
    smtp_host = config.get("alert_smtp_host", "smtp.gmail.com")
    smtp_port = config.get("alert_smtp_port", 587)

    if not smtp_user:
        print("  [email] no alert_email_from in config — skipping")
        return

    msg = MIMEText(text)
    msg["Subject"] = f"Heritage Canon Promo Alert — {date.today()}"
    msg["From"] = smtp_user
    msg["To"] = smtp_to

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        print(f"  [email] sent to {smtp_to}")
    except Exception as e:
        print(f"  [email] failed: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", action="store_true", help="Send alert email")
    parser.add_argument("--promote", action="store_true", help="Run promote.py if alerts found")
    args = parser.parse_args()

    config = load_config()
    print(f"[{date.today()}] Running daily monitor...")

    candidates = run_fast_sources(config)
    alerts = find_alerts(candidates)
    output = format_alerts(alerts)

    print(output)

    if alerts:
        Path("output").mkdir(exist_ok=True)
        Path(f"output/alerts_{date.today()}.txt").write_text(output)

        if args.email:
            send_email(output, config)

        if args.promote:
            # Save candidates for promote.py to consume
            Path("output/candidates.json").write_text(
                json.dumps(candidates, indent=2)
            )
            subprocess.run([sys.executable, "promote.py", "--mode", "alerts"])


if __name__ == "__main__":
    main()
