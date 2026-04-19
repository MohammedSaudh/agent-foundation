# Enable postponed evaluation of type hints.
from __future__ import annotations

# Import CSV support so the top alerts can be exported for manual review.
import csv
# Import Path so output folders and files can be handled cleanly.
from pathlib import Path

# Import the feed list and source metadata.
from config.sources import SOURCE_META, SOURCES
# Import the RSS fetcher that already exists in your project.
from src.ingest.rss import fetch_rss_articles
# Import the low-value filter.
from src.ranking.noise_filter import split_low_value_articles
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


# Export the top alerts into a CSV for manual review.
def export_review_csv(alerts: list[RankedAlert], output_path: str = "evaluation/top5_review.csv", top_k: int = 5) -> None:
    # Create the output folder if it does not already exist.
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Open the CSV file for writing.
    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        # Create a CSV writer object.
        writer = csv.writer(file)

        # Write the header row.
        writer.writerow([
            "rank",
            "article_id",
            "source",
            "title",
            "category",
            "importance_score",
            "novelty_score",
            "url",
            "label_signal_or_noise",
            "label_duplicate",
            "label_primary_source_quality",
            "notes",
        ])

        # Write one row per top alert.
        for idx, alert in enumerate(alerts[:top_k], start=1):
            writer.writerow([
                idx,
                alert.article.id,
                alert.article.source,
                alert.article.title,
                alert.category,
                alert.importance_score,
                alert.novelty_score,
                alert.article.url,
                "",
                "",
                "",
                "",
            ])


# Compute a simple manual-evaluation metric from a finished review CSV.
def compute_precision_at_k(review_csv_path: str = "evaluation/top5_review.csv") -> None:
    # Build the path object for the review file.
    path = Path(review_csv_path)

    # Stop early if the review file does not exist yet.
    if not path.exists():
        print("\nNo review CSV found yet, so Precision@5 cannot be computed.")
        return

    # Open the review CSV.
    with open(path, mode="r", newline="", encoding="utf-8") as file:
        # Read all rows into memory.
        rows = list(csv.DictReader(file))

    # Stop early if the file is empty.
    if not rows:
        print("\nReview CSV is empty, so Precision@5 cannot be computed.")
        return

    # Keep only rows where the label has been filled in.
    labeled_rows = [row for row in rows if row["label_signal_or_noise"].strip()]

    # Stop early if nothing has been labeled yet.
    if not labeled_rows:
        print("\nTop-5 review exported. Fill in the labels first, then rerun to compute Precision@5.")
        return

    # Count how many labeled rows are marked as research signal.
    signal_count = sum(
        1
        for row in labeled_rows
        if row["label_signal_or_noise"].strip().lower() == "research_signal"
    )

    # Compute precision using only the labeled rows.
    precision = signal_count / len(labeled_rows)

    # Print the metric.
    print(f"\nManual evaluation")
    print("=" * 80)
    print(f"Precision@{len(labeled_rows)} = {precision:.2f} ({signal_count}/{len(labeled_rows)})")


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
        compute_precision_at_k()
        return

    # Remove obvious low-value articles before ranking.
    filtered_articles, removed_articles = split_low_value_articles(new_articles)
    # Print how many were removed by the noise filter.
    print(f"Removed as low-value noise: {len(removed_articles)}")
    # Print how many remain after filtering.
    print(f"Articles remaining after noise filter: {len(filtered_articles)}")

    # Stop early if the noise filter removed everything.
    if not filtered_articles:
        print("All new articles were filtered out as low-value.")
        return

    # Load recent article history so novelty can be calculated against past content.
    history_texts = build_history_texts(limit=200)

    # Rank the filtered articles using source quality, impact, novelty, breadth, and urgency.
    ranked_alerts = rank_articles(
        articles=filtered_articles,
        history_texts=history_texts,
        source_meta=SOURCE_META,
    )

    # Insert the filtered articles into the database after scoring them.
    inserted = insert_articles(filtered_articles)
    # Print how many new articles were saved.
    print(f"Inserted {inserted} filtered articles into ingestion.db")

    # Print the top ranked research alerts in the terminal.
    print_alerts(ranked_alerts, top_k=5)

    # Export the current top 5 for manual review.
    export_review_csv(ranked_alerts, output_path="F:/Projects/aget-foundation/evaluation/top5_review.csv", top_k=5)
    print("\nExported top-5 review file to evaluation/top5_review.csv")

    # Try to compute Precision@K if the review file already contains labels.
    compute_precision_at_k()


# Run the main function only when this file is executed directly.
if __name__ == "__main__":
    # Start the pipeline.
    main()