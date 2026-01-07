from dataclasses import dataclass
from typing import Optional

# This file defines what an "Article" looks like in our project.
#
# We use this class as the single, standard format for all articles.
# Once data is turned into an Article:
# - all required fields must be present
# - the structure cannot change
# - the values cannot be edited later
#
# This helps us keep the system clean and predictable.
# Messy data is handled before creating an Article.
# Everything after that works only with clean data.

@dataclass(frozen=True)
class Article:
    id : str
    source : str
    title: str
    url : str
    published_at : Optional[str]
    excerpt: str