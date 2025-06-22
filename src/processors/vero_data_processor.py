# -*- coding: utf-8 -*-
from .data_processor import DataProcessor
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import logging
import os

class VeroDataProcessor(DataProcessor):
    """Concrete data processor for Vero market data."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.market_map = self._load_market_map()

    def _load_market_map(self) -> Dict[str, str]:
        """Loads the market code-to-name mapping file created by the scraper."""
        map_path = 'outputs/vero_market_map.json'
        if not os.path.exists(map_path):
            self.logger.warning(f"Market map file not found at {map_path}. Store names will be codes.")
            return {}
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load or parse market map at {map_path}: {e}")
            return {}

    def _get_category(self, description: str, product_name: str) -> Optional[str]:
        """Extracts the category from the product's description field.

        For the Vero market format, the category information is located in the
        'description' field of the raw data. This method cleans and returns
        that value.

        Args:
            description: The raw description string, which is assumed to be
                the category.
            product_name: The name of the product (used for logging).

        Returns:
            The category name as a string, or "Uncategorized" if not found.
        """
        if description and isinstance(description, str) and description.strip():
            return description.strip()
        else:
            self.logger.debug(f"No category found for product '{product_name}'. Defaulting to Uncategorized.")
            return "Uncategorized"

    def _create_store_location(self, store_name: str) -> str:
        """
        Looks up the full market name from the map using the market code
        extracted from the store_name (e.g., '89_1').
        """
        if not store_name:
            return "Unknown Store"
        
        market_code = store_name.split('_')[0]
        return self.market_map.get(market_code, store_name) # Fallback to the original store_name

    def process_market_data(self, file_path: str) -> pd.DataFrame:
        """
        Loads raw Vero data from a JSON file, processes it, filters for available items,
        and returns a clean DataFrame.
        """
        self.logger.info(f"Processing Vero data from: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Could not read or parse the file at {file_path}: {e}")
            return pd.DataFrame()

        processed_products = []
        for product in raw_data:
            # Check availability first to skip unavailable products
            is_available = self._extract_availability(product.get('достапност_во\nпродажен_објект', ''))
            if not is_available:
                continue
            
            # Process the available product
            clean_product_data = self.create_product_data(
                product_name=product.get('назив_на_стока'),
                current_price=product.get('продажна_цена\n(со_ддв)'),
                regular_price=product.get('редовна_цена\n(со_ддв)'),
                description=product.get('опис_на_стока'),
                price_per_unit=product.get('единечна_цена'),
                availability=product.get('достапност_во\nпродажен_објект'),
                store_name=product.get('market_code') # Use market_code from scraper
            )
            processed_products.append(clean_product_data)
        
        if not processed_products:
            self.logger.warning("No available products found to process.")
            return pd.DataFrame()

        # Create DataFrame from the list of dictionaries
        df = pd.DataFrame(processed_products)

        # Ensure the DataFrame has exactly the columns required, in the correct order
        # This will drop any extra columns and add any missing ones (with NaN)
        final_df = df.reindex(columns=self.FINAL_COLUMNS)

        self.logger.info(f"Successfully processed {len(final_df)} available products from {file_path}.")
        return final_df 