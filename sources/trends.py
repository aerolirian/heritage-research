"""
Google Trends scanner via pytrends (no API key required).
Identifies search momentum spikes for PD authors and themes.
"""
import time
from pytrends.request import TrendReq

AUTHOR_QUERIES = [
    ["Thomas Mann", "Knut Hamsun", "Sinclair Lewis", "Franz Kafka", "James Joyce"],
    ["Virginia Woolf", "Joseph Conrad", "F. Scott Fitzgerald", "Edith Wharton", "Willa Cather"],
    ["Ernest Hemingway", "William Faulkner", "John Steinbeck", "Theodore Dreiser", "Upton Sinclair"],
]


def scan(config):
    pytrends = TrendReq(hl="en-US", tz=0)
    candidates = []

    for batch in AUTHOR_QUERIES:
        try:
            pytrends.build_payload(batch, timeframe="now 3-m", geo="")
            interest = pytrends.interest_over_time()
            if interest.empty:
                continue
            for author in batch:
                if author not in interest.columns:
                    continue
                series = interest[author]
                avg = series.mean()
                recent = series.tail(4).mean()  # last ~month
                if avg > 0 and recent / avg > 1.3:  # 30% spike
                    candidates.append({
                        "source": "trends",
                        "author": author,
                        "title": "",
                        "trend_avg": round(float(avg), 1),
                        "trend_recent": round(float(recent), 1),
                        "trend_ratio": round(float(recent / avg), 2),
                        "why_now": f"Google Trends spike: {round(float(recent/avg), 1)}x above 3-month average",
                        "raw_score": min(100, float(recent)),
                    })
            time.sleep(2)  # avoid rate limiting
        except Exception as e:
            print(f"  [trends] {e}")

    return candidates
