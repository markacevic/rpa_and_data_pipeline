# -*- coding: utf-8 -*-
"""Data processor for the Zito market.

This module provides the data processor for Zito, which uses the
standard market data processing logic.
"""

from .standard_market_data_processor import StandardMarketDataProcessor

class ZitoDataProcessor(StandardMarketDataProcessor):
    """Concrete data processor for Zito Market.
    
    This class inherits all necessary processing logic from the 
    StandardMarketDataProcessor, as the raw data format from the Zito scraper
    matches the standard keys.
    """
    pass
