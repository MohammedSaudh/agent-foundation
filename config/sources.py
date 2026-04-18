# List of RSS feeds the pipeline will fetch from.
SOURCES = [
    # CoinDesk feed configuration.
    {
        # Human-readable source name.
        "name": "CoinDesk",
        # RSS feed URL for CoinDesk.
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
    },
    # Cointelegraph feed configuration.
    {
        # Human-readable source name.
        "name": "Cointelegraph",
        # RSS feed URL for Cointelegraph.
        "url": "https://cointelegraph.com/rss",
    },
    # CryptoSlate feed configuration.
    {
        # Human-readable source name.
        "name": "CryptoSlate",
        # RSS feed URL for CryptoSlate.
        "url": "https://cryptoslate.com/feed/",
    },
    # CryptoPotato feed configuration.
    {
        # Human-readable source name.
        "name": "CryptoPotato",
        # RSS feed URL for CryptoPotato.
        "url": "https://cryptopotato.com/feed/",
    },
    # CryptoNews feed configuration.
    {
        # Human-readable source name.
        "name": "CryptoNews",
        # RSS feed URL for CryptoNews.
        "url": "https://cryptonews.com/news/feed/",
    },
]

# Extra metadata used for source-aware scoring.
SOURCE_META = {
    # Metadata for CoinDesk.
    "CoinDesk": {
        # Treat this as secondary news coverage, not a primary project source.
        "source_type": "news_secondary",
        # Relative source quality score on a 0 to 1 scale.
        "source_quality": 0.75,
        # This source is not a primary source.
        "primary_source": False,
    },
    # Metadata for Cointelegraph.
    "Cointelegraph": {
        # Treat this as secondary news coverage.
        "source_type": "news_secondary",
        # Relative source quality score.
        "source_quality": 0.70,
        # This source is not a primary source.
        "primary_source": False,
    },
    # Metadata for CryptoSlate.
    "CryptoSlate": {
        # Treat this as secondary news coverage.
        "source_type": "news_secondary",
        # Relative source quality score.
        "source_quality": 0.65,
        # This source is not a primary source.
        "primary_source": False,
    },
    # Metadata for CryptoPotato.
    "CryptoPotato": {
        # Treat this as secondary news coverage.
        "source_type": "news_secondary",
        # Relative source quality score.
        "source_quality": 0.55,
        # This source is not a primary source.
        "primary_source": False,
    },
    # Metadata for CryptoNews.
    "CryptoNews": {
        # Treat this as secondary news coverage.
        "source_type": "news_secondary",
        # Relative source quality score.
        "source_quality": 0.55,
        # This source is not a primary source.
        "primary_source": False,
    },
}  