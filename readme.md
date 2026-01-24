# Agent Foundation

A learning project that builds an RSS-based agent which:
- collects articles from multiple sources
- normalizes them into a fixed internal format
- stores them in SQLite with deduplication
- ranks new articles by how much *new information* they contain

This repository intentionally starts with a **simple, rule-based baseline**
before introducing machine learning.

---

## Current Capabilities

- RSS ingestion from multiple sources
- Canonical `Article` data model
- Hash-based deduplication
- SQLite storage
- Baseline novelty ranking using text overlap
- Fully runnable end-to-end pipeline


## Project Structure
    ```
    src/
        ingest/     # RSS ingestion
        models/     # Core data models
        storage/    # SQLite persistence
        ranking/    # Novelty scoring (baseline)
    run.py          # Entry point

    ```

## Why a Baseline First?

Before using ML or LLMs, this project establishes:
- a clear objective ("new information")
- a measurable scoring function
- a clean data pipeline

Machine learning will later **replace only the ranking logic** —
everything else remains unchanged.

---

## Roadmap

Planned next steps:
- Crypto-only RSS feeds
- Improved novelty scoring (TF-IDF, embeddings)
- Lightweight local ML models
- Optional fine-tuning experiments

This repo is primarily a learning and experimentation ground.