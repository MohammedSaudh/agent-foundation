from src.ingest.rss import fetch_rss_articles
from src.storage.sqlite import init_db
from src.storage.sqlite import insert_articles
from src.storage.sqlite import get_recent_articles
from src.ranking.novelty import novelty_score
from src.storage.sqlite import get_existing_article_ids



if __name__ == "__main__":

    init_db()
    sources = [
        {"name": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"},
        {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
        {"name": "CryptoSlate",   "url": "https://cryptoslate.com/feed/"},
        {"name": "CryptoPotato",  "url": "https://cryptopotato.com/feed/"},
        {"name": "CryptoNews",    "url": "https://cryptonews.com/news/feed/"},
    ]

    articles = fetch_rss_articles(sources)

    # Keep only crypto-related articles (simple keyword filter)
    CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "xrp", "ripple",
    "bnb", "binance", "coinbase", "kraken", "bybit", "okx",
    "defi", "dex", "cex", "airdrop", "staking", "yield", "liquidity",
    "stablecoin", "usdt", "usdc", "tether", "circle",
    "etf", "sec", "cftc", "regulation",
    "wallet", "metamask", "ledger",
    "hack", "exploit", "rug", "bridge", "smart contract", "layer 2", "l2"
                        ]


    def is_crypto_article(a) -> bool:
        text = f"{a.title} {a.excerpt}".lower()
        return any(k in text for k in CRYPTO_KEYWORDS)
    
    articles = [a for a in articles if is_crypto_article(a)]
    print(f"after crypto filter: {len(articles)} articles ")

    # Remove posts we usually don't want in an "important news" alert
    LOW_VALUE_PHRASES = [
    "price prediction", "prediction:", "will it go", "could hit", "target",
    "symmetrical triangle", "breakout", "breakdown", "support", "resistance",
    "technical analysis", "chart", "signals", "today", "this week",
    "sponsored", "press release",
                        ]
    
    def is_low_value(a) -> bool:
        text = f"{a.title} {a.excerpt}".lower()
        return any(p in text for p in LOW_VALUE_PHRASES)
    
    before = len(articles)
    articles = [a for a in articles if not is_low_value(a)]
    print(f"after low value filter : {len(articles)} (removed {before -len(articles)})")


    existing_ids =  get_existing_article_ids([a.id for a in articles])
    new_articles = [a for a in articles if a.id not in existing_ids]
    print(f"new articles to rank : {len(new_articles)}")

    #build history text from stored articles
    history_articles = get_recent_articles(limit = 200)
    history_texts = [f"{a.title} {a.excerpt}" for a in history_articles]



    # Simple importance scoring (rule-based weights)
    IMPORTANCE_WEIGHTS = {
    # regulation / government
    "sec": 3.0, "cftc": 3.0, "regulation": 2.5, "bill": 2.0, "law": 2.0, "ban": 2.0,
    "court": 2.0, "lawsuit": 2.0, "fine": 2.0, "settlement": 2.0,

    # security incidents
    "hack": 3.0, "exploit": 3.0, "breach": 3.0, "drain": 2.5, "stolen": 2.5, "phishing": 2.0,

    # market structure / products
    "etf": 3.0, "approval": 2.0, "filing": 2.0,

    # protocol / tech changes
    "upgrade": 2.0, "fork": 2.0, "mainnet": 2.0, "testnet": 1.5, "launch": 1.5,

    # institutions / large moves
    "blackrock": 2.5, "coinbase": 1.5, "binance": 1.5, "kraken": 1.5,
                        }
    
    def importance_score(text: str) -> float:
        t = text.lower()
        score = 0.0
        for kw, w in IMPORTANCE_WEIGHTS.items():
            if kw in t :
                score += w
        
        return score


    scored = []
    for a in new_articles:
        text = f"{a.title} {a.excerpt}"
        nov = novelty_score(text, history_texts)
        imp = importance_score(text)

        final = (0.7 * nov) + (0.3 * min(1.0, imp/6.0))
        scored.append((final, nov, imp, a))

    scored.sort(key = lambda x: x[0], reverse = True)

    print("\nTop 5 new + important (baseline):")
    for final, nov, imp, a in scored[:5]:
        print(f"{final:.2f} (nov={nov:.2f}, imp={imp:.1f}) [{a.source}] {a.title}")

    inserted = insert_articles(new_articles)

    print(f"\nInserted {inserted} new articles into SQLite")
    print(f"Fetched {len(articles)} articles total from RSS")
    print(f"New articles detected before insert: {len(new_articles)}")

    recent = get_recent_articles(limit=10)
    print("\nLatest 10 articles in DB:")
    for a in recent:
        print(f"[{a.source}] {a.title} -> {a.url}")

    print("\nSample of first 5 fetched articles (after filters):")
    for a in articles[:5]:
        print(f"[{a.source}] {a.title} -> {a.url}")



