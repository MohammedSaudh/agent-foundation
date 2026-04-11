# Agent Foundation

A crypto-focused news intelligence project that ingests RSS feeds, filters noise, stores articles in SQLite, and ranks new articles by how much **new** and **important** information they contain.

This project started as a simple rule-based baseline and is now evolving into a more semantic, ML-assisted ranking pipeline.

---

## What the project does

- Ingests RSS feeds from major crypto news sources
- Normalizes articles into a fixed internal `Article` format
- Stores articles in SQLite with deterministic ID-based deduplication
- Filters out non-crypto and low-value content
- Scores articles on:
  - **Novelty** → how different the article is from recent history
  - **Importance** → rule-based weighting for regulation, security incidents, ETFs, institutional moves, and protocol changes
- Ranks only **newly seen** articles instead of re-ranking old history

---

## Current Capabilities

- RSS ingestion from multiple sources
- Canonical `Article` data model
- SQLite storage
- Hash-based deduplication
- Crypto-only filtering
- Low-value content filtering
- Baseline novelty scoring
- Embedding-based semantic novelty module
- Importance scoring using domain rules
- End-to-end runnable pipeline

---

## Project Structure
    ```
    src/
        ingest/     # RSS ingestion
        models/     # Core data models
        storage/    # SQLite persistence
        ranking/    # Novelty scoring (baseline)
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

- Fully switch ranking from lexical novelty to embedding-based novelty
- Cache embeddings for faster repeated runs
- Cluster articles into stories / events before ranking
- Add source-aware weighting
- Generate daily “what actually changed today” crypto digests
- Explore stronger embedding models and optional fine-tuning later

---

## Status

This is an active learning and experimentation project.

The current version already works end-to-end, and each new step is being added in small, testable increments.