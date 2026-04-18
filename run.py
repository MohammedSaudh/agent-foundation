# Enable postponed evaluation of type hints.
from __future__ import annotations

# Import the feed list and source metadata.
from config.sources import SOURCE_META, SOURCES
# Import the RSS fetcher that already exists in your project.
from src.ingest.rss import fetch_rss_articles
# Import the ranking function and ranked result type.
from src.ranking.importance import RankedAlert, rank_articles
# Import database helpers for setup, duplicate checking, insertion, and history loading.
from src.storage.sqlite import (
    get_existing_article_ids,
    get_recent_articles,
    init_db,
    insert_articles,
)


# Turn an article title and excerpt into one text block for novelty comparison.
def article_to_text(title: str, excerpt: str) -> str:
    # Combine title and excerpt with a newline in between.
    return f"{title}\n{excerpt}".strip()


# Build a history list from the most recent stored articles.
def build_history_texts(limit: int = 200) -> list[str]:
    # Load recent articles from the database.
    history_articles = get_recent_articles(limit=limit)
    # Convert each article into one combined text block.
    return [
        article_to_text(article.title, article.excerpt)
        for article in history_articles
        if article.title.strip()
    ]


# Print alert cards in a clean readable terminal format.
def print_alerts(alerts: list[RankedAlert], top_k: int = 5) -> None:
    # Stop early if there is nothing to print.
    if not alerts:
        print("\nNo alert cards to show.")
        return

    # Print a section heading.
    print("\nTop research alerts")
    # Print a divider line for readability.
    print("=" * 80)

    # Loop through only the top K alerts.
    for idx, alert in enumerate(alerts[:top_k], start=1):
        # Print rank number plus final importance score and category.
        print(f"\n{idx}. [{alert.importance_score}/10] {alert.category.upper()}")
        # Print the article source name.
        print(f"Source: {alert.article.source}")
        # Print whether this source is primary or secondary.
        print(f"Primary source: {'Yes' if alert.primary_source else 'No'}")
        # Print the article title.
        print(f"Title: {alert.article.title}")
        # Print a short explanation of why this may matter.
        print(f"Why it matters: {alert.why_it_matters}")
        # Print the novelty score.
        print(f"Novelty: {alert.novelty_score}/10")
        # Print the source quality score.
        print(f"Source quality: {alert.source_score}/10")
        # Print the research impact score.
        print(f"Research impact: {alert.research_impact_score}/10")
        # Print the breadth score.
        print(f"Breadth: {alert.breadth_score}/10")
        # Print the urgency score.
        print(f"Urgency: {alert.urgency_score}/10")
        # Print the article URL.
        print(f"URL: {alert.article.url}")


# Main entry point for the full research-alert pipeline.
def main() -> None:
    # Print a startup message so you know the script is actually running.
    print("Starting crypto research alert pipeline...")

    # Create the database tables if they do not already exist.
    init_db()

    # Fetch articles from all configured RSS feeds.
    fetched_articles = fetch_rss_articles(SOURCES)
    # Print how many articles were fetched.
    print(f"Fetched {len(fetched_articles)} articles from configured sources.")

    # Stop early if feed fetching returned nothing.
    if not fetched_articles:
        print("No articles fetched. Check feed URLs or network access.")
        return

    # Extract the IDs of all fetched articles.
    fetched_ids = [article.id for article in fetched_articles]
    # Ask the database which of these IDs already exist.
    existing_ids = get_existing_article_ids(fetched_ids)

    # Keep only articles that are not already in the database.
    new_articles = [article for article in fetched_articles if article.id not in existing_ids]
    # Print how many articles are actually new in this batch.
    print(f"New articles in this batch: {len(new_articles)}")

    # Stop early if there is nothing new to rank.
    if not new_articles:
        print("No new articles found. Nothing to rank right now.")
        return

    # Load recent article history so novelty can be calculated against past content.
    history_texts = build_history_texts(limit=200)

    # Rank the new articles using source quality, impact, novelty, breadth, and urgency.
    ranked_alerts = rank_articles(
        articles=new_articles,
        history_texts=history_texts,
        source_meta=SOURCE_META,
    )

    # Insert the new articles into the database after scoring them.
    inserted = insert_articles(new_articles)
    # Print how many new articles were saved.
    print(f"Inserted {inserted} new articles into ingestion.db")

    # Print the top ranked research alerts in the terminal.
    print_alerts(ranked_alerts, top_k=5)


# Run the main function only when this file is executed directly.
if __name__ == "__main__":
    # Start the pipeline.
    main()