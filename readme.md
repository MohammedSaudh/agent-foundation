# Agent Foundation

A crypto research alert pipeline designed to help researchers find genuinely important developments faster by filtering noise, deduplicating repeated coverage, and ranking new articles by novelty and research relevance.

## What it does

- Ingests RSS feeds from crypto news sources
- Normalizes articles into a fixed `Article` schema
- Stores articles in SQLite with deterministic ID-based deduplication
- Filters low-value content such as price analysis and roundup-style posts
- Scores new articles using novelty, importance, and source-aware signals
- Outputs structured research alerts for manual review

## Current capabilities

- RSS ingestion
- Canonical article model
- SQLite persistence
- Hash-based deduplication
- Low-value content filtering
- Semantic novelty scoring
- Rule-based importance scoring
- End-to-end runnable pipeline
- Review CSV export for manual evaluation

## Quick start


## Project Structure
    ```
    src/
        ingest/     # RSS ingestion
        models/     # Core data models
        storage/    # SQLite persistence
        ranking/    # scoring rules and logic
    run.py          # Entry point

    ```

## Current ML usage

This project does **not** train a custom model.

Instead, it uses:
- pretrained sentence embeddings for semantic similarity
- rule-based importance scoring for domain relevance

So the system is best described as a **hybrid pipeline**:
- engineering + filtering
- storage + deduplication
- rule-based ranking
- pretrained ML inference

---

## Roadmap

Planned next steps:

- Build a labeled dataset from pipeline outputs for researcher-signal vs noise classification
- Train a first-pass signal-vs-noise classifier to improve shortlist quality
- Improve event-level clustering so repeated coverage of the same story does not dominate results
- Add source-aware weighting to better separate primary sources from secondary coverage
- Move from rule-based importance scoring toward learned ranking
- Track shortlist-quality metrics such as Precision@5, noise rate, and duplicate rate
- Explore stronger embedding models and optional fine-tuning later

---

## Status

This is an active learning and experimentation project.

The current version already works end-to-end, and each new step is being added in small, testable increments.