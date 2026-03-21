import sqlite3  # Import the standard library for SQLite database interaction
from typing import List  # Import List for type hinting the article collections
from datetime import datetime, timezone  # Import datetime tools to handle UTC timestamps
from src.models.article import Article  # Import your custom Article data class/model
import uuid #Generate unique post ids
from urllib.parse import urlsplit, urlunsplit  #Clean UTM tracking params from URLs


def clean_url(url: str) -> str:  #remove query string + fragment to strip tracking paramters.
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))  #Rebuild url without query/Fragment.


def insert_post_draft(article_id: str, platform: str, content: str, db_path: str = "ingestion.db") -> str:  # Insert a draft post and return post_id
    conn = sqlite3.connect(db_path)  # Open DB connection
    post_id = str(uuid.uuid4())  # Create unique post id
    created_at_utc = datetime.now(timezone.utc).isoformat()  # Timestamp draft creation in UTC
    conn.execute(  # Insert draft row into posts
        """
        INSERT INTO posts (id, article_id, platform, content, status, created_at_utc)
        VALUES (?, ?, ?, ?, 'draft', ?)
        """,
        (post_id, article_id, platform, content, created_at_utc),
    )  # End insert
    conn.commit()  # Save changes
    conn.close()  # Close connection
    return post_id  # Return new post id


def get_draft_posts(limit: int = 50, db_path: str = "ingestion.db") -> list[sqlite3.Row]:  # Fetch draft posts joined with article context
    conn = sqlite3.connect(db_path)  # Open DB connection
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    rows = conn.execute(  # Select drafts + article context
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
    ).fetchall()  # Fetch all
    conn.close()  # Close connection
    return rows  # Return result rows


def review_post(post_id: str, decision: str, note: str = "", db_path: str = "ingestion.db") -> None:  # Approve or reject a draft post
    if decision not in {"approved", "rejected"}:  # Validate decision input
        raise ValueError("decision must be 'approved' or 'rejected'")  # Fail fast if invalid decision
    conn = sqlite3.connect(db_path)  # Open DB connection
    reviewed_at_utc = datetime.now(timezone.utc).isoformat()  # Timestamp review in UTC
    conn.execute(  # Update draft row to approved/rejected with review metadata
        """
        UPDATE posts
        SET status = ?, reviewed_at_utc = ?, reviewer_note = ?
        WHERE id = ? AND status = 'draft'
        """,
        (decision, reviewed_at_utc, note, post_id),
    )  # End update
    conn.commit()  # Save changes
    conn.close()  # Close connection



def ensure_columns(conn, table: str, required_cols: dict) -> None:  # Safely add missing columns to an existing table
    cur = conn.cursor()  # Create a cursor object to execute SQL commands
    cur.execute(f"PRAGMA table_info({table});")  # Query the database for the table's current structure
    rows = cur.fetchall()  # Retrieve all rows of metadata about the table's columns
    existing = {row[1] for row in rows}  # Create a set of column names that already exist

    for col, col_def in required_cols.items():  # Iterate through required columns and definitions
        if col not in existing:  # Check if the required column is missing from the table
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def};")  # Add the missing column using SQL ALTER


def init_posts_table(conn) -> None:  # Create posts table for customized drafts and later publishing (HITL workflow)
    conn.execute(  # Execute SQL to create posts table if it doesn't already exist
        """
        CREATE TABLE IF NOT EXISTS posts(
            id TEXT PRIMARY KEY,  -- Unique id for the post (uuid or hash)
            article_id TEXT NOT NULL,  -- Source article used for this post
            platform TEXT NOT NULL,  -- Platform: 'x' or 'linkedin'
            content TEXT NOT NULL,  -- Draft text content
            status TEXT NOT NULL CHECK(status IN ('draft','approved','queued','published','rejected','failed')),  -- HITL states
            created_at_utc TEXT NOT NULL,  -- When draft was created
            reviewed_at_utc TEXT,  -- When you reviewed it (approve/reject)
            reviewer_note TEXT,  -- Optional note you leave during review
            scheduled_at_utc TEXT,  -- When it should be posted
            published_at_utc TEXT,  -- When it was posted
            error TEXT,  -- Failure reason if failed
            FOREIGN KEY(article_id) REFERENCES articles(id)  -- Link back to article
        )
        """
    )  # End CREATE TABLE statement

    conn.execute(  # Create an index to speed up finding draft posts for review
        """
        CREATE INDEX IF NOT EXISTS idx_posts_status_created
        ON posts(status, created_at_utc)
        """
    )  # End CREATE INDEX statement


def init_db(db_path: str = "ingestion.db") -> None:  # Initialize database schema (articles + posts)
    conn = sqlite3.connect(db_path)  # Establish a connection to the SQLite database file

    conn.execute(  # Execute SQL to create articles table if it doesn't already exist
        """
        CREATE TABLE IF NOT EXISTS articles(
            id TEXT PRIMARY KEY,  -- Unique identifier for each article
            source TEXT NOT NULL,  -- Name of the news source (e.g., RSS feed name)
            title TEXT NOT NULL,  -- The headline of the article
            url TEXT NOT NULL,  -- The direct link to the news story
            published_at TEXT,  -- The date/time the article was originally published
            excerpt TEXT NOT NULL  -- A short summary or snippet of the content
        )
        """
    )  # End CREATE TABLE statement for articles

    ensure_columns(conn, "articles", {"ingested_at_utc": "TEXT"})  # Ensure ingestion timestamp column exists for older DBs

    init_posts_table(conn)  # Ensure posts table exists for human-in-the-loop review workflow

    conn.commit()  # Save all schema changes to the database
    conn.close()  # Close the database connection to free up resources


def insert_articles(articles: List[Article], db_path: str = "ingestion.db") -> int:  # Insert new articles and return how many were inserted
    conn = sqlite3.connect(db_path)  # Connect to the specified ingestion database

    ensure_columns(conn, "articles", {"ingested_at_utc": "TEXT"})  # Ensure column exists before inserting into it

    inserted = 0  # Initialize a counter to track how many new articles are saved
    ingested_now_utc = datetime.now(timezone.utc).isoformat()  # Generate a single UTC timestamp for the batch

    for article in articles:  # Loop through each article object provided in the list
        try:  # Use try/except to handle potential unique-constraint errors (duplicates)
            conn.execute(  # Execute insertion command using placeholders
                """
                INSERT INTO articles (id, source, title, url, published_at, excerpt, ingested_at_utc)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.id,  # The unique ID (usually a hash of the URL or title)
                    article.source,  # The origin of the article
                    article.title,  # The news headline
                    article.url,  # The web link
                    article.published_at,  # Original publication timestamp
                    article.excerpt,  # Brief text summary
                    ingested_now_utc,  # Our internal timestamp for when we found it
                ),
            )  # End insert execution

            inserted += 1  # Increment counter if insertion succeeded
        except sqlite3.IntegrityError:  # Catch error if the ID already exists in the database
            pass  # Skip duplicates and continue

    conn.commit()  # Commit all successful insertions to the database file
    conn.close()  # Close the connection
    return inserted  # Return the total count of new articles added to the system


def get_recent_articles(limit: int = 50, db_path: str = "ingestion.db") -> list[Article]:  # Fetch newest articles as Article objects
    conn = sqlite3.connect(db_path)  # Connect to the ingestion database
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects

    rows = conn.execute(  # Execute query to get newest articles
        """
        SELECT id, source, title, url, published_at, excerpt
        FROM articles
        ORDER BY COALESCE(published_at, ingested_at_utc) DESC  -- Sort by published time, fallback to ingested time
        LIMIT ?
        """,
        (limit,),
    ).fetchall()  # Fetch all rows

    conn.close()  # Close connection

    return [  # Convert rows to Article objects
        Article(
            id=r["id"],
            source=r["source"],
            title=r["title"],
            url=r["url"],
            published_at=r["published_at"],
            excerpt=r["excerpt"],
        )
        for r in rows
    ]  # Return list of articles


def get_existing_article_ids(ids: list[str], db_path: str = "ingestion.db") -> set[str]:  # Return which ids exist in DB already
    if not ids:  # Handle empty input quickly
        return set()  # Return empty set if nothing to check

    conn = sqlite3.connect(db_path)  # Connect to DB
    placeholders = ",".join(["?"] * len(ids))  # Build ?,?,? placeholders for SQL IN clause

    rows = conn.execute(  # Execute query to fetch existing ids
        f"SELECT id FROM articles WHERE id IN ({placeholders})",
        ids,
    ).fetchall()  # Fetch results

    conn.close()  # Close DB connection
    return {r[0] for r in rows}  # Return a set of existing ids


def insert_post_draft(article_id: str, platform: str, content: str, db_path: str = "ingestion.db") -> str:  # Insert a new post draft and return its id
    conn = sqlite3.connect(db_path)  # Open DB connection
    post_id = str(uuid.uuid4())  # Create a unique post id
    created_at_utc = datetime.now(timezone.utc).isoformat()  # Timestamp draft creation in UTC
    conn.execute(  # Insert a new row in posts as a draft
        """
        INSERT INTO posts (id, article_id, platform, content, status, created_at_utc)
        VALUES (?, ?, ?, ?, 'draft', ?)
        """,
        (post_id, article_id, platform, content, created_at_utc),
    )  # End insert
    conn.commit()  # Save changes
    conn.close()  # Close connection
    return post_id  # Return the created post id


def get_draft_posts(limit: int = 50, db_path: str = "ingestion.db") -> list[sqlite3.Row]:  # Fetch draft posts joined with article context for review
    conn = sqlite3.connect(db_path)  # Open DB connection
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    rows = conn.execute(  # Select draft posts plus relevant article fields
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
    ).fetchall()  # Fetch results
    conn.close()  # Close connection
    return rows  # Return rows for CLI printing


def review_post(post_id: str, decision: str, note: str = "", db_path: str = "ingestion.db") -> None:  # Approve or reject a draft post with an optional note
    if decision not in {"approved", "rejected"}:  # Validate decision input
        raise ValueError("decision must be 'approved' or 'rejected'")  # Fail fast on invalid input

    conn = sqlite3.connect(db_path)  # Open DB connection
    reviewed_at_utc = datetime.now(timezone.utc).isoformat()  # Timestamp the review action in UTC
    conn.execute(  # Update the post row with review outcome
        """
        UPDATE posts
        SET status = ?, reviewed_at_utc = ?, reviewer_note = ?
        WHERE id = ? AND status = 'draft'
        """,
        (decision, reviewed_at_utc, note, post_id),
    )  # End update
    conn.commit()  # Save changes
    conn.close()  # Close connection

