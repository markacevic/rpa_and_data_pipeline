"""
Scrapers Package.

This package contains all the web scraper implementations for different supermarket websites.
Each scraper is designed to extract product information such as name, price, and category.

The package provides a factory function `get_market_scraper` for conveniently creating
scraper instances based on the market name. Individual scraper classes are also exposed
for direct use if specific functionality is required.

Available Scrapers:
- VeroScraper
- TinexScraper
- ZitoScraper
- StokomakScraper
"""

# Import the scrapers
from .vero_scraper import VeroScraper
from .tinex_scraper import TinexScraper
from .zito_scraper import ZitoScraper
from .stokomak_scraper import StokomakScraper
from .factory import get_market_scraper

# Expose the scrapers and the factory function
__all__ = [
    "VeroScraper",
    "TinexScraper",
    "ZitoScraper",
    "StokomakScraper",
    "get_market_scraper",
]
