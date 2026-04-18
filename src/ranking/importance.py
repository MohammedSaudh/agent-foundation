# Enable postponed evaluation of type hints.
from __future__ import annotations

# Import dataclass to create a clean structured result object.
from dataclasses import dataclass

# Import the shared Article model used across the project.
from src.models.article import Article
# Import the existing novelty scorer so importance is not based only on keywords.
from src.ranking.novelty import novelty_score


# Map each category to a list of simple keywords used for rule-based classification.
CATEGORY_KEYWORDS = {
    # Keywords that usually indicate security-related developments.
    "security": [
        "exploit", "hack", "breach", "attack", "drained", "drain",
        "vulnerability", "incident", "stolen"
    ],
    # Keywords that usually indicate regulatory or legal developments.
    "regulation": [
        "sec", "cftc", "regulator", "regulation", "compliance",
        "lawsuit", "court", "legal", "approval", "ban"
    ],
    # Keywords that usually indicate governance developments.
    "governance": [
        "governance", "proposal", "vote", "voting", "snapshot",
        "delegate", "forum"
    ],
    # Keywords that usually indicate tokenomics-related developments.
    "tokenomics": [
        "tokenomics", "unlock", "vesting", "burn", "mint", "supply",
        "emission", "treasury", "airdrop", "inflation", "staking rewards"
    ],
    # Keywords that usually indicate technical infrastructure changes.
    "infrastructure": [
        "mainnet", "testnet", "upgrade", "release", "integration",
        "bridge", "oracle", "validator", "rollup", "rpc", "client"
    ],
    # Keywords that usually indicate fundraising or investment news.
    "funding": [
        "funding", "raised", "seed", "series a", "series b",
        "investment", "backed by"
    ],
    # Keywords that usually indicate exchange listing or delisting news.
    "listing": [
        "listing", "listed", "delisting", "trading pair", "trading pairs"
    ],
}

# Assign a base research-impact score to each category.
CATEGORY_BASE_IMPACT = {
    # Security issues are usually highly important for researchers.
    "security": 0.95,
    # Regulation is usually highly important for researchers.
    "regulation": 0.90,
    # Tokenomics changes often matter a lot for valuation and incentives.
    "tokenomics": 0.85,
    # Governance changes matter because they affect protocol direction.
    "governance": 0.80,
    # Infrastructure changes matter but are often slightly less urgent than exploits.
    "infrastructure": 0.75,
    # Funding matters, but usually less than core protocol changes.
    "funding": 0.60,
    # Listings matter, but usually carry less research depth.
    "listing": 0.55,
    # General uncategorized news gets a lower base score.
    "general": 0.35,
}

# Keywords that suggest the situation may be time-sensitive or urgent.
URGENCY_KEYWORDS = [
    "urgent", "emergency", "halted", "paused", "pause", "breach",
    "exploit", "lawsuit", "approval", "delisting", "attack"
]

# Keywords that suggest broader ecosystem relevance.
BREADTH_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "solana", "stablecoin",
    "binance", "coinbase", "etf", "validator", "bridge",
    "layer 2", "l2", "defi"
]


# Structured result object for a ranked research alert.
@dataclass(frozen=True)
class RankedAlert:
    # Original article object.
    article: Article
    # Detected category for the article.
    category: str
    # Final importance score on a 0 to 10 scale.
    importance_score: float
    # Novelty score on a 0 to 10 scale.
    novelty_score: float
    # Source quality score on a 0 to 10 scale.
    source_score: float
    # Research impact score on a 0 to 10 scale.
    research_impact_score: float
    # Breadth score on a 0 to 10 scale.
    breadth_score: float
    # Urgency score on a 0 to 10 scale.
    urgency_score: float
    # Whether the source is primary or not.
    primary_source: bool
    # Short explanation of why the article may matter.
    why_it_matters: str


# Assign a category based on simple keyword matching.
def classify_category(text: str) -> str:
    # Lowercase the text so matching is case-insensitive.
    lowered = text.lower()

    # Loop through each category and its keywords.
    for category, keywords in CATEGORY_KEYWORDS.items():
        # Return the first category whose keyword appears in the text.
        if any(keyword in lowered for keyword in keywords):
            return category

    # Fall back to general if no category matches.
    return "general"


# Assign an urgency score based on keyword hits.
def score_urgency(text: str) -> float:
    # Lowercase the text so matching is case-insensitive.
    lowered = text.lower()
    # Count how many urgency keywords appear in the text.
    hits = sum(1 for keyword in URGENCY_KEYWORDS if keyword in lowered)

    # Give the highest urgency score when multiple urgency clues are present.
    if hits >= 2:
        return 1.0
    # Give a medium-high urgency score when one urgency clue is present.
    if hits == 1:
        return 0.7
    # Give a low default urgency score otherwise.
    return 0.2


# Assign a breadth score based on how many broad-market keywords appear.
def score_breadth(text: str) -> float:
    # Lowercase the text so matching is case-insensitive.
    lowered = text.lower()
    # Count how many breadth keywords appear in the text.
    hits = sum(1 for keyword in BREADTH_KEYWORDS if keyword in lowered)

    # Give the highest breadth score when many broad-impact keywords appear.
    if hits >= 3:
        return 1.0
    # Give a strong breadth score when two keywords appear.
    if hits == 2:
        return 0.8
    # Give a moderate breadth score when one keyword appears.
    if hits == 1:
        return 0.6
    # Give a lower default breadth score otherwise.
    return 0.3


# Assign a research-impact score using category plus a few reinforcing keywords.
def score_research_impact(category: str, text: str) -> float:
    # Start from the base impact score for the detected category.
    base_score = CATEGORY_BASE_IMPACT.get(category, 0.35)
    # Lowercase the text so matching is case-insensitive.
    lowered = text.lower()

    # Slightly boost tokenomics stories when they mention especially important supply mechanics.
    if category == "tokenomics" and any(
        term in lowered for term in ["supply", "unlock", "burn", "mint", "treasury"]
    ):
        base_score += 0.05

    # Slightly boost governance stories when they mention direct voting mechanics.
    if category == "governance" and any(
        term in lowered for term in ["vote", "proposal", "delegate"]
    ):
        base_score += 0.05

    # Slightly boost infrastructure stories when they mention core network components.
    if category == "infrastructure" and any(
        term in lowered for term in ["mainnet", "upgrade", "validator", "bridge"]
    ):
        base_score += 0.05

    # Cap the score at 1.0 so it never exceeds the allowed range.
    return min(base_score, 1.0)


# Build a short explanation string for why the article might matter.
def build_why_it_matters(category: str, primary_source: bool) -> str:
    # Start the message by telling the user whether the source is primary or secondary.
    source_phrase = "Primary-source update." if primary_source else "Secondary coverage."

    # Category-specific explanation messages.
    category_messages = {
        "security": "Potential protocol or user-funds risk. Researchers should check scope and affected systems.",
        "regulation": "Could change compliance, market structure, or access assumptions.",
        "governance": "May change protocol direction, voting outcomes, or decision power.",
        "tokenomics": "Could affect supply, incentives, treasury expectations, or valuation assumptions.",
        "infrastructure": "May change protocol functionality, integrations, or network reliability.",
        "funding": "Can shift ecosystem incentives, runway, or competitive positioning.",
        "listing": "May affect access and liquidity, but usually carries less research depth than core protocol changes.",
        "general": "May be worth reviewing, but impact is less clearly defined.",
    }

    # Combine source context plus category explanation into one sentence block.
    return f"{source_phrase} {category_messages.get(category, category_messages['general'])}"


# Rank a batch of articles using source quality, impact, novelty, breadth, and urgency.
def rank_articles(
    articles: list[Article],
    history_texts: list[str],
    source_meta: dict[str, dict],
) -> list[RankedAlert]:
    # Create an empty list to collect ranked results.
    ranked: list[RankedAlert] = []

    # Loop through each new article we want to score.
    for article in articles:
        # Combine title and excerpt so classification and scoring use both.
        combined_text = f"{article.title}\n{article.excerpt}".strip()

        # Pull source metadata, or use a safe fallback if the source is unknown.
        meta = source_meta.get(
            article.source,
            {
                "source_type": "unknown",
                "source_quality": 0.50,
                "primary_source": False,
            },
        )

        # Classify the article into one of the scoring categories.
        category = classify_category(combined_text)
        # Read the source quality score from the metadata.
        source_score = float(meta["source_quality"])
        # Read whether this source is primary or secondary.
        primary_source = bool(meta["primary_source"])
        # Compute category-based research impact.
        impact_score = score_research_impact(category, combined_text)
        # Compute urgency score from text clues.
        urgency_score = score_urgency(combined_text)
        # Compute breadth score from ecosystem-wide clues.
        breadth_score = score_breadth(combined_text)
        # Compute novelty against recent stored article history.
        novelty = novelty_score(combined_text, history_texts)

        # Combine all dimensions into one final importance score.
        final_score = (
            0.30 * source_score
            + 0.25 * impact_score
            + 0.20 * novelty
            + 0.15 * breadth_score
            + 0.10 * urgency_score
        )

        # Give a small bonus when a primary source reports a high-value category directly.
        if primary_source and category in {
            "security",
            "regulation",
            "governance",
            "tokenomics",
            "infrastructure",
        }:
            final_score += 0.05

        # Cap the final score at 1.0 so it stays within range.
        final_score = min(final_score, 1.0)

        # Convert the scored article into a RankedAlert object and store it.
        ranked.append(
            RankedAlert(
                article=article,
                category=category,
                importance_score=round(final_score * 10, 2),
                novelty_score=round(novelty * 10, 2),
                source_score=round(source_score * 10, 2),
                research_impact_score=round(impact_score * 10, 2),
                breadth_score=round(breadth_score * 10, 2),
                urgency_score=round(urgency_score * 10, 2),
                primary_source=primary_source,
                why_it_matters=build_why_it_matters(category, primary_source),
            )
        )

    # Sort results from highest importance to lowest importance.
    ranked.sort(
        key=lambda item: (
            item.importance_score,
            item.novelty_score,
            item.source_score,
        ),
        reverse=True,
    )

    # Return the sorted list of ranked alerts.
    return ranked