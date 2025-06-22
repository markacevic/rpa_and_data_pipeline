# -*- coding: utf-8 -*-
from typing import Type, Dict
from .data_processor import DataProcessor
from .vero_data_processor import VeroDataProcessor
from .zito_data_processor import ZitoDataProcessor
from .tinex_data_processor import TinexDataProcessor
from .stokomak_data_processor import StokomakDataProcessor

# Mapping of market names to their corresponding data processor classes
PROCESSOR_MAP: Dict[str, Type[DataProcessor]] = {
    'vero': VeroDataProcessor,
    'zito': ZitoDataProcessor,
    'tinex': TinexDataProcessor,
    'stokomak': StokomakDataProcessor,
}

def get_data_processor(market_name: str) -> DataProcessor:
    """
    Factory function to get a data processor instance for a given market.

    Args:
        market_name: The name of the market (e.g., 'vero', 'zito').

    Returns:
        An instance of the appropriate DataProcessor subclass.

    Raises:
        ValueError: If the market_name is not supported.
    """
    market_name_lower = market_name.lower()
    processor_class = PROCESSOR_MAP.get(market_name_lower)

    if processor_class:
        return processor_class()
    else:
        raise ValueError(f"Unsupported market: '{market_name}'. No data processor found.") 