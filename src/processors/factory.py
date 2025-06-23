# -*- coding: utf-8 -*-
from typing import Type, Dict
from .data_processor import DataProcessor
from .vero_data_processor import VeroDataProcessor
from .zito_data_processor import ZitoDataProcessor
from .tinex_data_processor import TinexDataProcessor
from .stokomak_data_processor import StokomakDataProcessor

# Mapping of market names to their corresponding data processor classes
PROCESSOR_MAP: Dict[str, Type[DataProcessor]] = {
    "vero": VeroDataProcessor,
    "zito": ZitoDataProcessor,
    "tinex": TinexDataProcessor,
    "stokomak": StokomakDataProcessor,
}


def get_data_processor(market_name: str) -> DataProcessor:
    """
    Factory function to get a data processor instance for a given market.

    This function provides a centralized way to instantiate the appropriate
    data processor based on the market name. It supports all configured
    markets and returns a properly initialized processor instance ready
    for data processing operations.

    Args:
        market_name: The name of the market (e.g., 'vero', 'zito', 'tinex', 'stokomak').
            The name is case-insensitive and will be converted to lowercase.

    Returns:
        An instance of the appropriate DataProcessor subclass configured
        for the specified market.

    Raises:
        ValueError: If the market_name is not supported or not found in
            the PROCESSOR_MAP configuration.

    Example:
        >>> processor = get_data_processor('vero')
        >>> isinstance(processor, VeroDataProcessor)
        True
    """
    market_name_lower = market_name.lower()
    processor_class = PROCESSOR_MAP.get(market_name_lower)

    if processor_class:
        return processor_class()
    else:
        raise ValueError(
            f"Unsupported market: '{market_name}'. No data processor found."
        )
