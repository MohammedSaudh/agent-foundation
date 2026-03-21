from src.storage.sqlite import get_recent_articles, insert_post_draft, get_draft_posts  # Import helpers

articles = get_recent_articles(limit=1)  # Try to fetch one article
if not articles:  # Handle empty DB safely
    print("No articles found in DB. Run ingestion first.")  # Explain what to do next
else:  # We have at least one article
    a = articles[0]  # Take the most recent article
    post_id = insert_post_draft(a.id, "x", f"TEST DRAFT: {a.title}\n{a.url}")  # Insert a draft post
    print("Created draft post:", post_id)  # Print created draft id
    drafts = get_draft_posts(limit=5)  # Fetch some drafts for review
    for d in drafts:  # Loop drafts
        print(d["post_id"], d["platform"], d["created_at_utc"])  # Print a short summary line
