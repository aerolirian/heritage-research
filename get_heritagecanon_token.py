#!/usr/bin/env python3
"""
get_heritagecanon_token.py — Get OAuth 1.0a access token for @heritagecanon.

Run this once. It will:
1. Open an authorization URL — open it in your browser while logged in as @heritagecanon
2. Ask you to paste the PIN
3. Print the access token and secret to paste into ~/.heritage_research.json

Usage:
    python get_heritagecanon_token.py
"""
import json
from pathlib import Path
import tweepy

CONFIG_PATH = Path.home() / ".heritage_research.json"
config = json.loads(CONFIG_PATH.read_text())

auth = tweepy.OAuth1UserHandler(
    consumer_key=config["x_api_key"],
    consumer_secret=config["x_api_secret"],
    callback="oob",  # PIN-based flow
)

url = auth.get_authorization_url()
print(f"\n1. Open this URL in your browser while logged in as @heritagecanon:\n\n   {url}\n")
print("2. Click Authorize, then copy the PIN shown.\n")

pin = input("3. Paste the PIN here: ").strip()
auth.get_access_token(pin)

print(f"\nAdd these to ~/.heritage_research.json:\n")
print(f'  "x_heritagecanon_access_token": "{auth.access_token}",')
print(f'  "x_heritagecanon_access_token_secret": "{auth.access_token_secret}",')
