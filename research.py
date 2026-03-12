#!/usr/bin/env python3
"""
heritage-research — CLI entry point
Usage:
  python research.py sweep [--source reddit|tmdb|gutenberg|hn|trends|brave]
  python research.py report
  python research.py pd "Author Name" --death-year YEAR
"""
import argparse
import json
import os
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".heritage_research.json"


def load_config():
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}")
        print("Copy config.example.json to ~/.heritage_research.json and fill in your API keys.")
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def cmd_sweep(args, config):
    sources = args.source.split(",") if args.source else [
        "reddit", "hn", "gutenberg", "tmdb", "trends", "brave",
        "goodreads", "wikipedia", "anniversary", "youtube",
        "amazon", "tiktok", "instagram", "twitter",
        "letterboxd", "opensyllabus",
    ]
    all_candidates = []
    for source in sources:
        print(f"[{source}] scanning...")
        try:
            candidates = run_source(source, config)
            print(f"[{source}] {len(candidates)} candidates")
            all_candidates.extend(candidates)
        except Exception as e:
            print(f"[{source}] ERROR: {e}")

    from scoring import score_and_rank
    ranked = score_and_rank(all_candidates)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / "candidates.json"
    out_path.write_text(json.dumps(ranked, indent=2, ensure_ascii=False))
    print(f"\nWrote {len(ranked)} candidates → {out_path}")

    if not args.no_brief and ranked:
        from brief import generate_briefs
        top = ranked[:20]
        print(f"\nGenerating acquisition briefs for top {len(top)} candidates...")
        generate_briefs(top, config, output_dir / "report.md")
        print(f"Report → {output_dir / 'report.md'}")


def run_source(source, config):
    if source == "reddit":
        from sources.reddit_scanner import scan
    elif source == "hn":
        from sources.hn_scanner import scan
    elif source == "gutenberg":
        from sources.gutenberg import scan
    elif source == "tmdb":
        from sources.tmdb_scanner import scan
    elif source == "trends":
        from sources.trends import scan
    elif source == "brave":
        from sources.brave_scanner import scan
    elif source == "goodreads":
        from sources.goodreads_scanner import scan
    elif source == "wikipedia":
        from sources.wikipedia_scanner import scan
    elif source == "anniversary":
        from sources.anniversary_scanner import scan
    elif source == "youtube":
        from sources.youtube_scanner import scan
    elif source == "amazon":
        from sources.amazon_scanner import scan
    elif source == "tiktok":
        from sources.tiktok_scanner import scan
    elif source == "instagram":
        from sources.instagram_scanner import scan
    elif source == "twitter":
        from sources.twitter_scanner import scan
    elif source == "letterboxd":
        from sources.letterboxd_scanner import scan
    elif source == "opensyllabus":
        from sources.opensyllabus_scanner import scan
    else:
        raise ValueError(f"Unknown source: {source}")
    return scan(config)


def cmd_report(args, config):
    path = Path("output/candidates.json")
    if not path.exists():
        print("No candidates.json found. Run: python research.py sweep")
        return
    candidates = json.loads(path.read_text())
    print(f"\n{'='*70}")
    print(f"HERITAGE RESEARCH — {len(candidates)} candidates")
    print(f"{'='*70}\n")
    for i, c in enumerate(candidates[:20], 1):
        print(f"{i:2}. [{c.get('score', 0):.1f}] {c['author']} — {c['title']}")
        print(f"    Why now: {c.get('why_now', '')}")
        print(f"    Angle:   {c.get('subtitle_angle', '')}")
        print()


def cmd_pd(args, config):
    from copyright import check_pd
    result = check_pd(args.author, args.death_year)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Heritage research pipeline")
    sub = parser.add_subparsers(dest="command")

    p_sweep = sub.add_parser("sweep", help="Run weekly research sweep")
    p_sweep.add_argument("--source", help="Comma-separated sources (default: all)")
    p_sweep.add_argument("--no-brief", action="store_true", help="Skip GPT brief generation")

    p_report = sub.add_parser("report", help="Display last sweep results")

    p_pd = sub.add_parser("pd", help="Check public domain status for an author")
    p_pd.add_argument("author", help="Author name")
    p_pd.add_argument("--death-year", type=int, required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    config = load_config()
    if args.command == "sweep":
        cmd_sweep(args, config)
    elif args.command == "report":
        cmd_report(args, config)
    elif args.command == "pd":
        cmd_pd(args, config)


if __name__ == "__main__":
    main()
