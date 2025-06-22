# -*- coding: utf-8 -*-
from .standard_market_data_processor import StandardMarketDataProcessor

class StokomakDataProcessor(StandardMarketDataProcessor):
    """
    Concrete data processor for Stokomak Market.
    
    This class inherits all necessary processing logic from the 
    StandardMarketDataProcessor, as the raw data format from the Stokomak scraper
    matches the standard keys defined in the base class.
    """
    pass 