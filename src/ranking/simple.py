def text_similarity(a: str, b: str) -> float:
    """
    Very simple similarity score based on shared words.
    Returns a value between 0 and 1.
    """
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())

    if not set_a or not set_b:
        return 0.0

    overlap = set_a.intersection(set_b)
    return len(overlap) / max(len(set_a), len(set_b))