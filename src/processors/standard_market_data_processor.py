# -*- coding: utf-8 -*-
"""Data processor for standard markets like Zito and Stokomak.

This module defines a processor that handles the common data structure
found across several markets. It relies on a generic JSON structure and
implements the category and store location logic suitable for these sites.
"""

import pandas as pd
from typing import Optional
import logging
import json
import os

from .data_processor import DataProcessor


class StandardMarketDataProcessor(DataProcessor):
    """Processes data for markets with a standard JSON format.

    This class is designed to work with the common data structure produced
    by the `BaseMarketScraper`. It implements the abstract methods from
    `DataProcessor` with logic tailored to this standard format. For these
    markets, the category is taken directly from the 'description' field.
    """
    def __init__(self):
        """Initializes the StandardMarketDataProcessor."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Standard Market Data Processor initialized.")

    def process_market_data(self, file_path: str) -> pd.DataFrame:
        """Loads data from a JSON file and processes it into a DataFrame.

        This method reads a list of product dictionaries from the specified
        JSON file, processes each one into a standardized format using the
        `create_product_data` method from the base class, and compiles
        them into a single pandas DataFrame.

        Args:
            file_path: The path to the input JSON file.

        Returns:
            A pandas DataFrame containing the cleaned and standardized
            product data, ready for validation and analysis. Returns an
            empty DataFrame if the file is not found or is empty.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Could not read or parse the data file at {file_path}: {e}")
            return pd.DataFrame()

        if not raw_data:
            self.logger.warning(f"No data found in {file_path}.")
            return pd.DataFrame()

        clean_data = []
        for item in raw_data:
            processed_item = self.create_product_data(
                product_name=item.get('назив_на_стока-производ'),
                current_price=item.get('продажна_цена'),
                regular_price=item.get('редовна_цена'),
                description=item.get('опис_на_стока'),
                price_per_unit=item.get('единечна_цена'),
                availability=item.get('достапност_во_продажен_објект'),
                store_name=item.get('market_name')
            )
            clean_data.append(processed_item)

        return pd.DataFrame(clean_data)

    def _get_category(self, description: str, product_name: str) -> Optional[str]:
        """Extracts the category from the product's description.

        For the standard market format, the category information is expected
        to be in the 'description' field. This method cleans and returns that
        value. If the description is missing, it logs a warning and defaults
        to "Uncategorized".

        Args:
            description: The raw description string, which is assumed to be
                the category.
            product_name: The name of the product (used for logging).

        Returns:
            The category name as a string, or "Uncategorized" if not found.
        """
        if description and isinstance(description, str) and description.strip():
            return description.strip()
        
        self.logger.debug(f"No category found for product '{product_name}'. Defaulting to Uncategorized.")
        return "Uncategorized"

    def _create_store_location(self, store_name: str) -> str:
        """Returns the store name directly as the location.

        In the standard market format, the 'store_name' field already
        represents the desired location (e.g., a specific branch). This
        method simply returns it after stripping any whitespace.

        Args:
            store_name: The name of the store/branch.

        Returns:
            The cleaned store name to be used as the location.
        """
        return store_name.strip() if store_name else "Unknown Location" 