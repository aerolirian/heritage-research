"""
OpenSyllabus scanner — which PD texts are taught in university lit/philosophy courses.
Academic teaching = sustained institutional demand + student audience.
No public API — scrapes the Explorer tool at opensyllabus.org via Playwright.
Email them at info@opensyllabus.org for API access (they're a non-profit, usually receptive).
"""
from playwright.sync_api import sync_playwright

OPENSYLLABUS_EXPLORER = "https://opensyllabus.org/result-lists/titles?size=500&field=Humanities"


def scan(config):
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })

        try:
            page.goto(OPENSYLLABUS_EXPLORER, timeout=30000)
            page.wait_for_timeout(5000)

            # Try to extract ranked titles from the explorer table
            rows = page.evaluate("""
                () => Array.from(document.querySelectorAll('tr, .result-row, [class*="row"]'))
                .slice(0, 200)
                .map(el => ({
                    text: el.innerText,
                    rank: el.querySelector('[class*="rank"], td:first-child')?.innerText || '',
                }))
                .filter(r => r.text.length > 10)
            """)

            for i, row in enumerate(rows):
                text = row.get("text", "")
                rank = row.get("rank", str(i + 1))

                # Filter for PD-era authors
                for author_last in ["Mann", "Kafka", "Joyce", "Dostoevsky", "Tolstoy",
                                    "Woolf", "Conrad", "Flaubert", "Chekhov", "Zola",
                                    "Hardy", "Dickens", "Austen", "Eliot", "Balzac"]:
                    if author_last.lower() in text.lower():
                        candidates.append({
                            "source": "opensyllabus",
                            "author": author_last,
                            "title": "",
                            "syllabus_rank": rank,
                            "why_now": f"Taught in university courses (OpenSyllabus rank #{rank})",
                            "raw_score": max(10, 60 - i * 0.3),
                        })
                        break

        except Exception as e:
            print(f"  [opensyllabus] {e} — try emailing info@opensyllabus.org for API access")

        browser.close()

    return candidates
