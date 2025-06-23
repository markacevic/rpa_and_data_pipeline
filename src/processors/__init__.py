# -*- coding: utf-8 -*-
"""Initializes the processors package and sets the public API.

This file makes the processor classes and the factory function available
for import from the `src.processors` package and defines the `__all__`
variable to specify which names are part of the public API.
"""

from .data_processor import DataProcessor
from .vero_data_processor import VeroDataProcessor
from .zito_data_processor import ZitoDataProcessor
from .standard_market_data_processor import StandardMarketDataProcessor
from .tinex_data_processor import TinexDataProcessor
from .stokomak_data_processor import StokomakDataProcessor
from .factory import get_data_processor

# This is a list of all the processors that are available in the module and can be imported
__all__ = [
    "DataProcessor",
    "VeroDataProcessor",
    "ZitoDataProcessor",
    "StandardMarketDataProcessor",
    "TinexDataProcessor",
    "StokomakDataProcessor",
    "get_data_processor",
]
