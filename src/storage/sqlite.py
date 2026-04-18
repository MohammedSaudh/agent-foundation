import sqlite3  # Import SQLite support from the standard library.
from typing import List  # Import List for typing article collections.
from datetime import datetime, timezone  # Import UTC timestamp helpers.
from urllib.parse import urlsplit, urlunsplit  # Import URL parsing helpers.
import uuid  # Import UUID generator for draft post IDs.

from src.models.article import Article  # Import the shared Article model.


def clean_url(url: str) -> str:
    # Split the URL into parts so query strings and fragments can be removed.
    parts = urlsplit(url)
    # Rebuild the URL without query parameters and fragments.
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def ensure_columns(conn, table: str, required_cols: dict) -> None:
    # Create a cursor to inspect the table schema.
    cur = conn.cursor()
    # Read the current list of columns from the SQLite table metadata.
    cur.execute(f"PRAGMA table_info({table});")
    # Fetch all returned schema rows.
    rows = cur.fetchall()
    # Build a set of existing column names for quick lookup.
    existing = {row[1] for row in rows}

    # Loop through every required column definition.
    for col, col_def in required_cols.items():
        # Add the column only if it does not already exist.
        if col not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def};")


def init_posts_table(conn) -> None:
    # Create the posts table if it does not already exist.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts(
            id TEXT PRIMARY KEY,
            article_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('draft','approved','queued','published','rejected','failed')),
            created_at_utc TEXT NOT NULL,
            reviewed_at_utc TEXT,
            reviewer_note TEXT,
            scheduled_at_utc TEXT,
            published_at_utc TEXT,
            error TEXT,
            FOREIGN KEY(article_id) REFERENCES articles(id)
        )
        """
    )

    # Create an index to speed up draft/review lookups by status and creation time.
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_posts_status_created
        ON posts(status, created_at_utc)
        """
    )


def init_db(db_path: str = "ingestion.db") -> None:
    # Open a connection to the SQLite database file.
    conn = sqlite3.connect(db_path)

    # Create the articles table if it does not already exist.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles(
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            published_at TEXT,
            excerpt TEXT NOT NULL
        )
        """
    )

    # Make sure older databases also have the ingestion timestamp column.
    ensure_columns(conn, "articles", {"ingested_at_utc": "TEXT"})

    # Make sure the posts table also exists.
    init_posts_table(conn)

    # Save schema changes.
    conn.commit()
    # Close the database connection.
    conn.close()


def insert_articles(articles: List[Article], db_path: str = "ingestion.db") -> int:
    # Open a connection to the SQLite database.
    conn = sqlite3.connect(db_path)

    # Make sure older databases also have the ingestion timestamp column.
    ensure_columns(conn, "articles", {"ingested_at_utc": "TEXT"})

    # Start a counter for successfully inserted new rows.
    inserted = 0
    # Generate one batch timestamp for this ingestion run.
    ingested_now_utc = datetime.now(timezone.utc).isoformat()

    # Loop through every article passed into the function.
    for article in articles:
        try:
            # Insert the article into the database.
            conn.execute(
                """
                INSERT INTO articles (id, source, title, url, published_at, excerpt, ingested_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.id,
                    article.source,
                    article.title,
                    article.url,
                    article.published_at,
                    article.excerpt,
                    ingested_now_utc,
                ),
            )

            # Increase the inserted counter if the insert succeeds.
            inserted += 1

        except sqlite3.IntegrityError:
            # Skip duplicate article IDs instead of crashing the pipeline.
            pass

    # Save all successful inserts.
    conn.commit()
    # Close the connection.
    conn.close()
    # Return how many new rows were inserted.
    return inserted


def get_recent_articles(limit: int = 50, db_path: str = "ingestion.db") -> list[Article]:
    # Open a connection to the SQLite database.
    conn = sqlite3.connect(db_path)
    # Return rows as dict-like objects instead of tuples.
    conn.row_factory = sqlite3.Row

    # Read the most recent articles, falling back to ingested_at_utc when published_at is missing.
    rows = conn.execute(
        """
        SELECT id, source, title, url, published_at, excerpt
        FROM articles
        ORDER BY COALESCE(published_at, ingested_at_utc) DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    # Close the connection.
    conn.close()

    # Convert database rows back into Article objects.
    return [
        Article(
            id=row["id"],
            source=row["source"],
            title=row["title"],
            url=row["url"],
            published_at=row["published_at"],
            excerpt=row["excerpt"],
        )
        for row in rows
    ]


def get_existing_article_ids(ids: list[str], db_path: str = "ingestion.db") -> set[str]:
    # Return early if the caller passed an empty list.
    if not ids:
        return set()

    # Open a connection to the SQLite database.
    conn = sqlite3.connect(db_path)

    # Build the correct number of placeholders for the SQL IN clause.
    placeholders = ",".join(["?"] * len(ids))

    # Fetch the subset of IDs that already exist in the articles table.
    rows = conn.execute(
        f"SELECT id FROM articles WHERE id IN ({placeholders})",
        ids,
    ).fetchall()

    # Close the connection.
    conn.close()

    # Return the existing IDs as a set for fast membership checks.
    return {row[0] for row in rows}


def insert_post_draft(article_id: str, platform: str, content: str, db_path: str = "ingestion.db") -> str:
    # Open a connection to the SQLite database.
    conn = sqlite3.connect(db_path)

    # Generate a unique ID for the draft post.
    post_id = str(uuid.uuid4())
    # Generate a UTC timestamp for when the draft was created.
    created_at_utc = datetime.now(timezone.utc).isoformat()

    # Insert the draft post into the posts table.
    conn.execute(
        """
        INSERT INTO posts (id, article_id, platform, content, status, created_at_utc)
        VALUES (?, ?, ?, ?, 'draft', ?)
        """,
        (post_id, article_id, platform, content, created_at_utc),
    )

    # Save the insert.
    conn.commit()
    # Close the connection.
    conn.close()

    # Return the generated draft post ID.
    return post_id


def get_draft_posts(limit: int = 50, db_path: str = "ingestion.db") -> list[sqlite3.Row]:
    # Open a connection to the SQLite database.
    conn = sqlite3.connect(db_path)
    # Return rows as dict-like objects.
    conn.row_factory = sqlite3.Row

    # Fetch draft posts along with their related article context.
    rows = conn.execute(
        """
        SELECT
            p.id AS post_id,
            p.platform,
            p.content,
            p.created_at_utc,
            a.id AS article_id,
            a.source,
            a.title,
            a.url,
            a.published_at
        FROM posts p
        JOIN articles a ON a.id = p.article_id
        WHERE p.status = 'draft'
        ORDER BY p.created_at_utc DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    # Close the connection.
    conn.close()

    # Return the fetched draft rows.
    return rows


def review_post(post_id: str, decision: str, note: str = "", db_path: str = "ingestion.db") -> None:
    # Reject invalid review decisions immediately.
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be 'approved' or 'rejected'")

    # Open a connection to the SQLite database.
    conn = sqlite3.connect(db_path)

    # Generate a UTC timestamp for when the review happened.
    reviewed_at_utc = datetime.now(timezone.utc).isoformat()

    # Update the draft post with the review outcome.
    conn.execute(
        """
        UPDATE posts
        SET status = ?, reviewed_at_utc = ?, reviewer_note = ?
        WHERE id = ? AND status = 'draft'
        """,
        (decision, reviewed_at_utc, note, post_id),
    )

    # Save the update.
    conn.commit()
    # Close the connection.
    conn.close()