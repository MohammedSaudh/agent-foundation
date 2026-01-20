from src.ingest.rss import fetch_rss_articles
from src.storage.sqlite import init_db
from src.storage.sqlite import insert_articles
from src.storage.sqlite import get_recent_articles
from src.ranking.novelty import novelty_score



if __name__ == "__main__":

    init_db()
    sources = [
        {"name":"Hacker News", "url":"https://news.ycombinator.com/rss"},
        {"name": "BBC World", "url":"http://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "Coin Desk","url":"https://www.coindesk.com/arc/outboundfeeds/rss?outputType=xml"}
    ]

    articles = fetch_rss_articles(sources)

    #build history text from stored articles
    history_articles = get_recent_articles(limit = 200)
    history_texts = [f"{a.title} {a.excerpt}" for a in history_articles]

    scored = []
    for a in articles:
        text = f"{a.title} {a.excerpt}"
        score = novelty_score(text, history_texts)
        scored.append((score, a))

    scored.sort(key = lambda x: x[0], reverse = True)

    print("\n Top 5 most 'new information' asticles (simple baseline):")
    for score, a in scored[:5]:
        print(f"{score:.2f} [{a.source}] {a.title}")

    inserted = insert_articles(articles)    

    recent = get_recent_articles(limit = 10)
    print("\n Latest 10 articles in DB")
    for a in recent:
        print(f"[{a.source}] {a.title} -> {a.url}")
    print(f" Inserted {inserted} new articles into SQLite")

    print(f"fetched {len(articles)} articles")

    for a in articles[:5]:
        print(f"[{a.source}] {a.title} -> {a.url}")



