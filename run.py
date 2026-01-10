from src.ingest.rss import fetch_rss_articles

if __name__ == "__main__":
    sources = [
        {"name":"Hacker News", "url":"https://news.ycombinator.com/rss"},
        {"name": "BBC World", "url":"http://feeds.bcci.co.uk/news/world/rss.xml"},
    ]

    articles = fetch_rss_articles(sources)

    print(f"fetched {len(articles)} articles")

    for a in articles[:5]:
        print(f"[{a.source}] {a.title} -> {a.url}")



        