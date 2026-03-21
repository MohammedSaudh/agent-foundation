from src.ingest.rss import fetch_rss_articles  # RSS ingestion
from src.storage.sqlite import init_db  # DB init
from src.storage.sqlite import insert_articles  # DB insert
from src.storage.sqlite import get_recent_articles  # DB read
from src.storage.sqlite import get_existing_article_ids  # Dedup against DB
from src.ranking.embedding import embedding_novelty_score, embed_texts  # Embedding novelty scoring
from src.storage.sqlite import insert_post_draft  # Save drafts into posts table
from src.storage.sqlite import clean_url  # Strip tracking params for nice links

DB_PATH = "ingestion.db"  # Single source of truth for where the pipeline reads/writes data

def draft_x_post(a) -> str:  # Create a short X draft from an article
    url = clean_url(a.url)  # Clean tracking params
    title = (a.title or "").strip()  # Normalize title
    return f"{title}\n\n{url}"  # Simple, clean X format


def draft_linkedin_post(a) -> str:  # Create a LinkedIn-style draft from an article
    url = clean_url(a.url)  # Clean tracking params
    title = (a.title or "").strip()  # Normalize title
    excerpt = (a.excerpt or "").strip()  # Normalize excerpt
    excerpt = excerpt[:350].rstrip()  # Keep it readable and not too long
    return f"{title}\n\n{excerpt}\n\nRead: {url}"  # Simple LinkedIn format


if __name__ == "__main__":  # Run the pipeline when executing this file directly

    init_db(DB_PATH)  # Ensure tables exist in ingestion.db

    sources = [  # RSS sources list
        {"name": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"},
        {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
        {"name": "CryptoSlate",   "url": "https://cryptoslate.com/feed/"},
        {"name": "CryptoPotato",  "url": "https://cryptopotato.com/feed/"},
        {"name": "CryptoNews",    "url": "https://cryptonews.com/news/feed/"},
    ]  # End sources list

    articles = fetch_rss_articles(sources)  # Fetch from RSS feeds

    CRYPTO_KEYWORDS = [  # Simple keyword filter for crypto relevance
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "xrp", "ripple",
        "bnb", "binance", "coinbase", "kraken", "bybit", "okx",
        "defi", "dex", "cex", "airdrop", "staking", "yield", "liquidity",
        "stablecoin", "usdt", "usdc", "tether", "circle",
        "etf", "sec", "cftc", "regulation",
        "wallet", "metamask", "ledger",
        "hack", "exploit", "rug", "bridge", "smart contract", "layer 2", "l2"
    ]  # End keywords

    def is_crypto_article(a) -> bool:  # Decide if article is crypto-related
        text = f"{a.title} {a.excerpt}".lower()  # Combine text fields for matching
        return any(k in text for k in CRYPTO_KEYWORDS)  # True if any keyword matches

    articles = [a for a in articles if is_crypto_article(a)]  # Keep only crypto-related
    print(f"after crypto filter: {len(articles)} articles")  # Log count

    LOW_VALUE_PHRASES = [  # Filter out low-signal content (TA/predictions/sponsored)
        "price prediction", "prediction:", "will it go", "could hit", "target",
        "symmetrical triangle", "breakout", "breakdown", "support", "resistance",
        "technical analysis", "chart", "signals", "today", "this week",
        "sponsored", "press release",
    ]  # End low-value phrases

    def is_low_value(a) -> bool:  # Decide if an article is low-value
        text = f"{a.title} {a.excerpt}".lower()  # Combine text fields for matching
        return any(p in text for p in LOW_VALUE_PHRASES)  # True if any low-value phrase matches

    before = len(articles)  # Count before filtering
    articles = [a for a in articles if not is_low_value(a)]  # Remove low-value
    print(f"after low value filter: {len(articles)} (removed {before - len(articles)})")  # Log delta

    existing_ids = get_existing_article_ids([a.id for a in articles], db_path=DB_PATH)  # Read existing IDs from ingestion.db
    new_articles = [a for a in articles if a.id not in existing_ids]  # Keep only truly new
    print(f"new articles to rank: {len(new_articles)}")  # Log new count

    history_articles = get_recent_articles(limit=200, db_path=DB_PATH)  # Pull recent history from ingestion.db
    history_texts = [f"{a.title} {a.excerpt}" for a in history_articles]  # Build text corpus for novelty
    history_embeddings = embed_texts(history_texts) if history_texts else None  # Pre-embed history if available

    IMPORTANCE_WEIGHTS = {  # Rule-based importance weights
        "sec": 3.0, "cftc": 3.0, "regulation": 2.5, "bill": 2.0, "law": 2.0, "ban": 2.0,
        "court": 2.0, "lawsuit": 2.0, "fine": 2.0, "settlement": 2.0,
        "hack": 3.0, "exploit": 3.0, "breach": 3.0, "drain": 2.5, "stolen": 2.5, "phishing": 2.0,
        "etf": 3.0, "approval": 2.0, "filing": 2.0,
        "upgrade": 2.0, "fork": 2.0, "mainnet": 2.0, "testnet": 1.5, "launch": 1.5,
        "blackrock": 2.5, "coinbase": 1.5, "binance": 1.5, "kraken": 1.5,
    }  # End weights

    def importance_score(text: str) -> float:  # Compute importance score from keyword weights
        t = text.lower()  # Normalize to lowercase
        score = 0.0  # Start at zero
        for kw, w in IMPORTANCE_WEIGHTS.items():  # Loop weights
            if kw in t:  # If keyword appears
                score += w  # Add weight
        return score  # Return importance score

    scored = []  # Collect (final, novelty, importance, article)
    for a in new_articles:  # Rank each new article
        text = f"{a.title} {a.excerpt}"  # Combine article text
        nov = embedding_novelty_score(text, history_texts, history_embeddings)  # Novelty vs history
        imp = importance_score(text)  # Importance from weights
        final = (0.7 * nov) + (0.3 * min(1.0, imp / 6.0))  # Combine novelty + normalized importance
        scored.append((final, nov, imp, a))  # Store result

    scored.sort(key=lambda x: x[0], reverse=True)  # Sort by final score descending

    TOP_N_DRAFTS = 3  # How many top-ranked articles to draft posts for
    for final, nov, imp, a in scored[:TOP_N_DRAFTS]:  # Loop through top N ranked new articles
        insert_post_draft(a.id, "x", draft_x_post(a), db_path=DB_PATH)  # Save X draft for review
        insert_post_draft(a.id, "linkedin", draft_linkedin_post(a), db_path=DB_PATH)  # Save LinkedIn draft for review

    print("\nTop 5 new + important (baseline):")  # Header
    for final, nov, imp, a in scored[:5]:  # Print top 5
        print(f"{final:.2f} (nov={nov:.2f}, imp={imp:.1f}) [{a.source}] {a.title}")  # One-line summary

    inserted = insert_articles(new_articles, db_path=DB_PATH)  # Insert new articles into ingestion.db

    print(f"\nInserted {inserted} new articles into SQLite")  # Log inserted count
    print(f"Fetched {len(articles)} articles total from RSS")  # Log fetched count
    print(f"New articles detected before insert: {len(new_articles)}")  # Log new detected count

    recent = get_recent_articles(limit=10, db_path=DB_PATH)  # Read latest 10 from ingestion.db
    print("\nLatest 10 articles in DB:")  # Header
    for a in recent:  # Loop recents
        print(f"[{a.source}] {a.title} -> {a.url}")  # Print summary

    print("\nSample of first 5 fetched articles (after filters):")  # Header
    for a in articles[:5]:  # Loop sample
        print(f"[{a.source}] {a.title} -> {a.url}")  # Print sample line
