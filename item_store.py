"""
ItemStore: Manages caching and wiki fetching for item metadata.

Provides persistent caching of item values (high_alch, bars_used) with lazy
wiki fetching. New items are fetched on-demand and saved to cache.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List


class ItemStore:
    """Manages item value caching and lazy wiki fetching."""

    def __init__(self, cache_path: str = "item_data.json"):
        """
        Initialize ItemStore with cache file path.

        Args:
            cache_path: Path to persistent cache JSON file
        """
        self.cache_path = Path(cache_path)
        self.data: Dict[str, Dict[str, Optional[int]]] = {}
        self.wiki_scraper = None  # Lazy-loaded on first miss

    def load(self) -> None:
        """Load item data from cache file. Creates empty cache if file doesn't exist."""
        if self.cache_path.exists():
            with open(self.cache_path, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def save(self) -> None:
        """Persist current item data to cache file."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def get_item_values(self, item_name: str) -> Dict[str, Optional[int]]:
        """
        Get high_alch and bars_used for an item.

        If item is in cache, return cached values. Otherwise, fetch from wiki,
        save to cache, and return.

        Args:
            item_name: Name of item to look up

        Returns:
            Dict with keys 'high_alch' and 'bars_used', values are int or None
        """
        # Return cached value if available
        if item_name in self.data:
            return self.data[item_name]

        # Lazy-load wiki scraper on first miss
        if self.wiki_scraper is None:
            from wiki_scraper import OSRSWikiScraper

            self.wiki_scraper = OSRSWikiScraper()

        # Fetch from wiki
        item_data = self.wiki_scraper.get_item_data(item_name)

        # Cache result (even if None values) and save
        self.data[item_name] = item_data
        self.save()

        return item_data

    def get_all_items(self, item_names: List[str]) -> Dict[str, Dict[str, Optional[int]]]:
        """
        Get values for multiple items.

        Batch operation for efficiency. Loads all items, fetching from wiki
        as needed and saving to cache.

        Args:
            item_names: List of item names to look up

        Returns:
            Dict mapping item_name to {high_alch, bars_used}
        """
        results = {}
        for item_name in item_names:
            results[item_name] = self.get_item_values(item_name)
        return results

    def _calculate_derived_values(
        self, high_alch: Optional[int], bars_used: Optional[int]
    ) -> Optional[int]:
        """
        Calculate Giant's Foundry value from bars used.

        Giants Foundry value = bars_used - 1 (one bar is consumed per progress bar segment).
        Returns None if bars_used is not available.

        Args:
            high_alch: High alch value (for reference, not used in calculation)
            bars_used: Number of bars required to make item

        Returns:
            Giants Foundry value (bars_used - 1) or None
        """
        if bars_used is None:
            return None
        return bars_used - 1
