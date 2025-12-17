"""
WikiScraper: Fetches item metadata from OSRS wiki API.

Uses MediaWiki API to retrieve item pages and regex to extract high_alch values
and bars_used for item crafting (Giant's Foundry context).
"""

import re
from typing import Dict, Optional

try:
    import requests
except ImportError:
    requests = None


class OSRSWikiScraper:
    """Fetches item data from OSRS wiki using MediaWiki API."""

    BASE_URL = "https://oldschool.runescape.wiki/api.php"
    TIMEOUT = 5

    def __init__(self):
        """Initialize scraper. Raises ImportError if requests not available."""
        if requests is None:
            raise ImportError(
                "requests library required for wiki scraping. "
                "Install with: pip install requests"
            )

    def get_item_data(self, item_name: str) -> Dict[str, Optional[int]]:
        """
        Get high_alch and bars_used for an item.

        Args:
            item_name: Name of item (exact match from wiki)

        Returns:
            Dict with keys 'high_alch' and 'bars_used', values are int or None.
            Returns {high_alch: None, bars_used: None} on error.
        """
        try:
            wikitext = self._fetch_wikitext(item_name)
            if wikitext is None:
                return {"high_alch": None, "bars_used": None}

            high_alch = self._extract_high_alch(wikitext)
            bars_used = self._extract_bars_used(wikitext)

            return {"high_alch": high_alch, "bars_used": bars_used}
        except Exception:
            # Silently fail with None values; let caller decide error handling
            return {"high_alch": None, "bars_used": None}

    def _fetch_wikitext(self, item_name: str) -> Optional[str]:
        """
        Fetch raw wikitext from OSRS wiki API.

        Args:
            item_name: Name of item to fetch

        Returns:
            Raw wikitext content or None if not found
        """
        params = {
            "action": "query",
            "titles": item_name,
            "prop": "wikitext",
            "format": "json",
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Extract wikitext from API response
            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})

            if "missing" in page:
                return None

            return page.get("wikitext", "")
        except Exception:
            return None

    def _extract_high_alch(self, wikitext: str) -> Optional[int]:
        """
        Extract high alch value from wikitext.

        Looks for patterns like:
        |high alch = 1920
        |highalch = 780

        Args:
            wikitext: Raw wikitext from wiki page

        Returns:
            High alch value as int, or None if not found
        """
        # Match "high alch" or "highalch" (case-insensitive) with value
        pattern = r"\|\s*high\s*alch\s*=\s*(\d+)"
        match = re.search(pattern, wikitext, re.IGNORECASE)

        if match:
            return int(match.group(1))

        return None

    def _extract_bars_used(self, wikitext: str) -> Optional[int]:
        """
        Extract bars_used for Giant's Foundry from wikitext.

        Looks for patterns like:
        |bars required = 2
        |bars = 3

        Args:
            wikitext: Raw wikitext from wiki page

        Returns:
            Number of bars required, or None if not found
        """
        # Match "bars required" or similar (case-insensitive) with value
        pattern = r"\|\s*bars\s+(?:required|used)\s*=\s*(\d+)"
        match = re.search(pattern, wikitext, re.IGNORECASE)

        if match:
            return int(match.group(1))

        # Fallback: look for just "bars =" in crafting context
        pattern = r"\|\s*bars\s*=\s*(\d+)"
        match = re.search(pattern, wikitext, re.IGNORECASE)

        if match:
            return int(match.group(1))

        return None
