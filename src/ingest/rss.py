from __future__ import annotations                                               # Helps Python handle type hints better
import hashlib                                                                   #Hashlib for article ID generation
from collections.abc import Iterable, Mapping                                    #Import generic collection protocols for flexible typed inputs.
from typing import Any                                                           #import Any because feed entries can contain mixed value types
import feedparser                                                                #import feedparser to fetch and parse RSS/ atom feeds
from dateutil import parser as date_parser                                       #import Dateutils parser to helper to normalize messy date formats 
from src.models.article import Article                                           #import the canonical internal article model

def _stable_article_id(source_name:str, url:str) -> str:                         # Build a stable article ID from the source name and URL.
    return hashlib.sha256(f"{source_name}:{url}".encode("utf-8")).hexdigest()    # Return the SHA-256 hash of the source-name/URL pair.

def _parse_published_at(entry: Mapping[str, Any]) -> str | None:                 # Parse a feed entry's published or updated timestamp into ISO-8601 format.
    raw_date = entry.get("published") or entry.get("updated") or ""              # Prefer the published field, then updated, and fall back to an empty string.
    if not raw_date:                                                             # return none immediately when the entry does not include a usable date
        return None
    try:                                                                         # Attempt to parse the raw date string
        return date_parser.parse(str(raw_date)).isoformat()                      # Return the normalized ISO-8601 representation.
    except (TypeError, ValueError, OverflowError):                               # Treat malformed or unsupported dates as missing instead of failing the pipeline. 
        return None                                                              # Return None when parsing fails.
    
def _to_article(source_name: str, entry:Mapping[str, Any]) -> Article |  None:   # Convert a single parsed feed entry into the project's Article model.
    title = str(entry.get("title", "")).strip()                                  # Read and normalize the entry title.
    url = str(entry.get("link", "")).strip()                                     # Read and normalize the entry link. 
    if not title or not url:                                                     # Skip entries that do not have the minimum fields required by the pipeline.
        return None  
    return Article(                                                              # Build and return the normalized immutable Article object.
        id = _stable_article_id(source_name, url),                               # Use a deterministic ID so duplicates are easy to detect.
        source = source_name,                                                    # Preserve the source name.
        title = title,                                                           # Preserve the normalized title.
        url= url,                                                                # Preserve the normalized URL.
        published_at= _parse_published_at(entry),                                # Store the parsed publish timestamp when available.
        excerpt = str(entry.get("summary", "")).strip()                          # Store the parsed publish timestamp when available.

    )

def fetch_rss_articles(sources: Iterable[Mapping[str, str]]) -> list[Article]:   # Fetch and normalize articles from all configured RSS sources.
    articles_by_id: dict[str, Article] = {}                                      # Use a dictionary keyed by article ID to deduplicate entries across sources and repeated feed items.
    for source in sources:
        source_name = source.get("name", "").strip()                             # Read and normalize the configured source name.
        source_url = source.get("url", "").strip()                               # Read and normalize the configured source URL.
        if not source_name or not source_url:                                    # Skip incomplete source configurations.
            continue
        feed = feedparser.parse(source_url)                                      # Parse the remote RSS/Atom feed.
        for entry in getattr(feed, "entries", []):                               # Iterate over the feed entries if they exist.
            article = _to_article(source_name, entry)                            # Convert the raw feed entry into the internal Article model.
            if article is not None:                                              # Keep the article only when conversion succeeded.
                articles_by_id.setdefault(article.id, article)                   # Preserve the first version seen for each stable article ID.

    return list(articles_by_id.values())                                         # Return the deduplicated normalized articles as a list.