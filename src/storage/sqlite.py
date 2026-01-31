import sqlite3
from typing import List
from src.models.article import Article

def init_db(db_path: str = "data.db") -> None:
    conn = sqlite3.connect(db_path)

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

    conn.commit()
    conn.close()

def insert_articles(articles: List[Article], db_path: str = "data.db") -> int:
    conn = sqlite3.connect(db_path)

    inserted = 0

    for article in articles:
        try:
            conn.execute(
                """
                INSERT INTO articles (id, source, title, url, published_at, excerpt)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    article.id,
                    article.source,
                    article.title,
                    article.url,
                    article.published_at,
                    article.excerpt,
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

    return inserted

def get_recent_articles(limit: int = 50, db_path: str = "data.db") -> list[Article]:
    conn = sqlite3.connect(db_path)

    conn.row_factory = sqlite3.Row

    rows = conn.execute(

        """
        SELECT id, source, title, url, published_at, excerpt
        FROM articles
        ORDER BY published_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    articles = []
    for r in rows:
        articles.append(
            Article(
                id = r['id'],
                source = r['source'],
                title = r['title'],
                url = r['url'],
                published_at = r['published_at'],
                excerpt = r['excerpt'],

            )
        )

    return articles


def get_existing_article_ids(ids: list[str], db_path: str = "data.db") -> set[str]:
    if not ids:
        return set()
    
    conn = sqlite3.connect(db_path)
    placeholders = ",".join(["?"] * len(ids))

    rows = conn.execute(
            f"SELECT id FROM articles WHERE id IN ({placeholders})",
            ids,

        ).fetchall()
    
    conn.close()
    return {r[0] for r in rows}