# Enable postponed evaluation of type hints.
from __future__ import annotations

# Import the shared Article model used across the project.
from src.models.article import Article


# These phrases usually indicate low-value content for crypto researchers.
LOW_VALUE_KEYWORDS = [
    # Generic roundup / recap patterns.
    "what happened in crypto today",
    "crypto today",
    "market roundup",
    "daily roundup",
    "weekly roundup",
    "morning briefing",
    "evening update",

    # Price prediction / trading chatter.
    "price prediction",
    "price analysis",
    "technical analysis",
    "trader says",
    "analyst says",
    "bullish",
    "bearish",
    "could reach",
    "set to rally",
    "set to surge",
    "may hit",
    "target price",
    "buy signal",
    "sell signal",

    # General market-noise phrasing.
    "market sentiment",
    "top gainers",
    "top losers",
    "why is bitcoin up",
    "why is bitcoin down",
    "why is ethereum up",
    "why is ethereum down",
    "should you buy",
    "should you sell",

    # Low-value engagement bait.
    "everything you need to know",
    "what to know",
    "here’s what to know",
]


# These phrases are not always noise, but often indicate weak research value.
SOFT_NOISE_KEYWORDS = [
    "surges",
    "soars",
    "jumps",
    "drops",
    "falls",
    "slumps",
    "rally",
    "crash",
    "breakout",
    "outlook",
]


# Check whether an article looks like low-value content.
def is_low_value_article(article: Article) -> bool:
    # Combine title and excerpt into one lowercase text block.
    text = f"{article.title}\n{article.excerpt}".lower().strip()

    # Immediately reject clearly low-value phrases.
    if any(keyword in text for keyword in LOW_VALUE_KEYWORDS):
        return True

    # Count how many softer noise signals appear.
    soft_hits = sum(1 for keyword in SOFT_NOISE_KEYWORDS if keyword in text)

    # If several soft-noise signals appear together, treat it as low-value.
    if soft_hits >= 2:
        return True

    # Otherwise keep the article.
    return False


# Split a batch of articles into kept vs removed groups.
def split_low_value_articles(articles: list[Article]) -> tuple[list[Article], list[Article]]:
    # Prepare output lists.
    kept_articles: list[Article] = []
    removed_articles: list[Article] = []

    # Check each article one by one.
    for article in articles:
        # Send low-value articles to the removed list.
        if is_low_value_article(article):
            removed_articles.append(article)
        # Keep everything else.
        else:
            kept_articles.append(article)

    # Return both lists so the caller can inspect counts.
    return kept_articles, removed_articles