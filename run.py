from __future__ import annotations                                                           # Allows using type hints without needing classes/functions to be defined beforehand
import hashlib                                                                               #For deterministic article id generation
from collections.abc import Iterable, Mapping                                                #Generic collection protocols for flexible typed inputs
from typing import Any                                                                       #BEcause feed entries can contain mixed value types
import feedparser                                                                            #to fetch and parse RSS/Atom datafeeds
from dateutil import parser as date_parser                                                   #to help normalize messy date formats 
from src.models.article import Article                                                       #Canonical internal Article model


def _stable_article_id(source_name: str, url: str) -> str:                                   #Build stable article id from source name and url
    return hashlib.sha256(f"{source_name}:{url}".encode("utf-8")).hexdigest()                #return SHA-256 hashname of the source-name/URl pair

def _parse_publised_at(entry: Mapping[str, Any]) -> str | None:                              #Parse a feed entry's published or updated timestamp into ISO-8601 format.
    raw_date = entry.get("published") or entry.get("updated") or ""                          #Prefer the published field, then updated, and fall back to an empty string.
    if not raw_date: 
        return None
    try:
        return date_parser.parse(str(raw_date)).isoformat()                                  #Return the normalized ISO-8601 representation.
    except (TypeError, ValueError, OverflowError):                                           #Treat malformed or unsupported dates as missing instead of failing the pipeline.
        return None
    
def _to_article(source_name: str, entry:Mapping[str, Any]) -> Article | None:                #Convert a single parsed feed entry into the project's Article model.
    title = str(entry.get("title", "")).strip()
    url = str(entry.get("link", "")).strip()
    if not title or url:
        return None
    
    return Article (                                                                         #Build and return the normalized immutable Article object.
        id = _stable_article_id(source_name, url),
        source = source_name,
        title = title,
        url = url,
        published_at = _parse_publised_at(entry),
        excerpt = str(entry.get("summary", "")).strip(),
    )


def fetch_rss_articles(sources: Iterable[Mapping[str, str]]) -> list[Article]:              # Fetch and normalize articles from all configured RSS sources.
    articles_by_id: dict[str, Article] = {}                                                 # Use a dictionary keyed by article ID to deduplicate entries across sources and repeated feed items.
    for source in sources:
        source_name = source.get("name", "").strip()
        source_url = source.get("url", "").strip()
        if not source_name or not source_url:
            continue
        feed = feedparser.parse(source_url)
        for entry in getattr(feed, "entries", []):
            article = _to_article(source_name, entry)
            if article is not None:
                articles_by_id.setdefault(article.id, article)

    return list(articles_by_id.values())