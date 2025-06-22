# -*- coding: utf-8 -*-
from .standard_market_data_processor import StandardMarketDataProcessor
from typing import Optional
class TinexDataProcessor(StandardMarketDataProcessor):
    """
    Concrete data processor for Tinex Market.
    
    This class inherits all necessary processing logic from the 
    StandardMarketDataProcessor, as the raw data format from the Tinex scraper
    matches the standard keys defined in the base class.
    """
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
        
        # Fallback 
        return "Uncategorized" 