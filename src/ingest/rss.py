import hashlib #makes a stable ID from (source + url), useful later for deduplication
import feedparser # reads RSS feed URLS and gives us entries (title/Link/ etc)

from dateutil import parser as date_parser #converts messy  date strings into standard format

from src.models.article import Article #our fixed shape for an aeticle inside this project


def fetch_rss_articles(sources):
    """
    Takes a list of RSS sources (each source has atleast: name, url).
    returns a list of Article objects
    """
    articles = []

    for source in sources:
        # Read the RSS feed from the source URL
        try:
            feed = feedparser.parse(source["url"])

        except Exception:
            continue

        # Each feed contains multiple articles (entries)
        for entry in feed.entries:
            title = entry.get("title", "")
            url = entry.get("link", "")
            # Skip entries that do not have a title or a link
            if not title or not url:
                continue

            #Create a stable ID using source name + article URL
            article_id = hashlib.sha256(f"{source['name']}:{url}".encode("utf-8")).hexdigest()

            #try to read the published date (may be missing or messy)
            published_at = None
            raw_date = entry.get("published", "")

  
            if raw_date:
                try:
                    published_at = date_parser.parse(raw_date).isoformat()
                except Exception:
                    published_at = None
            
            article = Article(
                id = article_id,
                source = source["name"],
                title = title.strip(),
                url = url.strip(),
                published_at = published_at,
                excerpt = entry.get("summary", "").strip()

            )
            articles.append(article)



    return articles