"""
Main package for the supermarket price checker.

This package contains the core functionality for scraping, processing, and validating
supermarket data from various sources. It provides a modular architecture for adding
new markets and data sources while maintaining consistency in data handling.
"""

from .scrapers import get_market_scraper
from .processors import get_data_processor
from .validators import DataValidator

__all__ = [
    'get_market_scraper',
    'get_data_processor',
    'DataValidator'
]