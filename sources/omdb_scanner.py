"""
OMDB scanner — existing film/TV adaptations of PD literary works.
Aggregates Rotten Tomatoes + Metacritic scores, plot data, awards.
Signals: adaptation quality (bad adaptation = intro can critique it), audience sentiment,
recent releases that could drive book interest.
Free API at omdbapi.com — just needs an email registration.
"""
import requests

OMDB_API = "http://www.omdbapi.com/"

# PD works with known film/TV adaptations to check
ADAPTATION_SEARCHES = [
    ("Wuthering Heights", "Emily Brontë"),
    ("Crime and Punishment", "Fyodor Dostoevsky"),
    ("Anna Karenina", "Leo Tolstoy"),
    ("Madame Bovary", "Gustave Flaubert"),
    ("The Trial", "Franz Kafka"),
    ("The Great Gatsby", "F. Scott Fitzgerald"),
    ("Death in Venice", "Thomas Mann"),
    ("A Portrait of the Artist as a Young Man", "James Joyce"),
    ("The Sun Also Rises", "Ernest Hemingway"),
    ("Mrs Dalloway", "Virginia Woolf"),
    ("The Picture of Dorian Gray", "Oscar Wilde"),
    ("Dracula", "Bram Stoker"),
    ("Frankenstein", "Mary Shelley"),
    ("The Count of Monte Cristo", "Alexandre Dumas"),
    ("Les Misérables", "Victor Hugo"),
    ("War and Peace", "Leo Tolstoy"),
    ("The Brothers Karamazov", "Fyodor Dostoevsky"),
    ("Heart of Darkness", "Joseph Conrad"),
    ("The Metamorphosis", "Franz Kafka"),
    ("Growth of the Soil", "Knut Hamsun"),
]


def scan(config):
    api_key = config.get("omdb_api_key", "")
    if not api_key:
        print("  [omdb] no api key — skipping (get free key at omdbapi.com)")
        return []

    candidates = []

    for title, author in ADAPTATION_SEARCHES:
        try:
            # Search for the title
            resp = requests.get(OMDB_API, params={
                "apikey": api_key,
                "t": title,
                "type": "movie",
            }, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("Response") == "True":
                imdb_rating = data.get("imdbRating", "N/A")
                rt_rating = next(
                    (r["Value"] for r in data.get("Ratings", []) if r["Source"] == "Rotten Tomatoes"),
                    "N/A"
                )
                year = data.get("Year", "")
                awards = data.get("Awards", "")

                # Bad adaptations are as interesting as good ones — intro can engage critically
                candidates.append({
                    "source": "omdb",
                    "author": author,
                    "title": title,
                    "adaptation_title": data.get("Title", title),
                    "adaptation_year": year,
                    "imdb_rating": imdb_rating,
                    "rt_rating": rt_rating,
                    "awards": awards,
                    "omdb_plot": data.get("Plot", "")[:200],
                    "why_now": f"Film adaptation ({year}): IMDB {imdb_rating}, RT {rt_rating} — intro can engage/critique",
                    "raw_score": 35,
                })

        except Exception as e:
            print(f"  [omdb/{title}] {e}")

    return candidates
