# -*- coding: utf-8 -*-
from .data_processor import DataProcessor
import pandas as pd
import json
from typing import Dict, Any, Optional
import logging
import re

class StandardMarketDataProcessor(DataProcessor):
    """
    A base processor for markets that share a standard raw data format
    (e.g., Zito, Tinex, Stokomak).
    
    You will need to update the KEY placeholders with the actual field names
    from the raw data.
    """
    
    # 
    PRODUCT_NAME_KEY = 'назив_на_стока-производ'
    CURRENT_PRICE_KEY = 'продажна_цена'
    REGULAR_PRICE_KEY = 'редовна_цена'
    DESCRIPTION_KEY = 'опис_на_стока'
    PRICE_PER_UNIT_KEY = 'единечна_цена'
    AVAILABILITY_KEY = 'достапност_во_продажен_објект'
    STORE_NAME_KEY = 'market_name'
    # --------------------------------------------------------------------------

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_category(self, description: str, product_name: str) -> Optional[str]:
        """
        For standard markets, we assume the category can be inferred from the product name.
        This is a placeholder and may need more specific logic.
        """
        # can be extended with more keywords 
        name_upper = product_name.upper()
        if any(keyword in name_upper for keyword in ["ЈОГУРТ", "МЛЕКО", "СИРЕЊЕ", "КАШКАВАЛ", "ЗДЕНКА", "ПАВЛАКА", "КАЈМАК"]):
            return "Млечни производи"
        if any(keyword in name_upper for keyword in ["ЛЕБ", "ПЕЦИВО", "БАГЕТ", "КРОАСАН", "PIJALOK"]):
            return "Леб и пецива"
        if any(keyword in name_upper for keyword in ["ПИВО", "ВИНО", "СОК", "ВОДА", "ПИЈАЛОК", "ВИСКИ", "КОЊАК", "ВОДКА", "ЛИКЕР", "РАКИЈА","РУМ", "ЏИН"]):
            return "Пијалоци"
        
        # Fallback to the description if it exists
        return description if description else "Uncategorized"

    def _create_store_location(self, store_name: str) -> str:
        """
        For standard markets, the store location is the identifier itself.
        """
        return store_name if store_name else "Unknown"

    def process_market_data(self, file_path: str) -> pd.DataFrame:
        """
        Loads raw data using the standard key mappings, processes it, 
        filters for available items, and returns a clean DataFrame.
        """
        self.logger.info(f"Processing standard market data from: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Could not read or parse file at {file_path}: {e}")
            return pd.DataFrame()

        processed_products = []
        for product in raw_data:
            # Check availability first
            is_available = self._extract_availability(product.get(self.AVAILABILITY_KEY, ''))
            if not is_available:
                continue
            
            # Process the available product using the key mappings
            clean_product_data = self.create_product_data(
                product_name=product.get(self.PRODUCT_NAME_KEY),
                current_price=product.get(self.CURRENT_PRICE_KEY),
                regular_price=product.get(self.REGULAR_PRICE_KEY),
                description=product.get(self.DESCRIPTION_KEY),
                price_per_unit=product.get(self.PRICE_PER_UNIT_KEY),
                availability=product.get(self.AVAILABILITY_KEY),
                store_name=product.get(self.STORE_NAME_KEY)
            )
            processed_products.append(clean_product_data)
        
        self.logger.info(f"Successfully processed {len(processed_products)} available products.")
        
        if not processed_products:
            self.logger.warning("No available products found to process.")
            return pd.DataFrame()

        # Create DataFrame from the list of dictionaries
        df = pd.DataFrame(processed_products)

        # Ensure the DataFrame has exactly the columns required, in the correct order
        final_df = df.reindex(columns=self.FINAL_COLUMNS)

        self.logger.info(f"Final DataFrame has {len(final_df)} records.")
        return final_df 