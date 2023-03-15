"""Provide common data types for the frozen_examples."""
from typing import OrderedDict


class Examples:
    """Represent frozen_examples and counter-frozen_examples of something textual."""

    def __init__(
        self, positives: OrderedDict[str, str], negatives: OrderedDict[str, str]
    ) -> None:
        """Initialize with the given values."""
        self.positives = positives
        self.negatives = negatives
