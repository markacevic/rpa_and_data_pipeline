# -*- coding: utf-8 -*-
"""Abstract base class and core logic for data processing.

This module defines the `DataProcessor` abstract base class, which provides a
common interface and shared functionality for processing product data from
different markets. It includes methods for data standardization, price and
unit calculations, and requires subclasses to implement market-specific logic.
"""
import pandas as pd
from typing import Dict, Any, Optional
import re
from abc import ABC, abstractmethod
import os

class DataProcessor(ABC):
    """Abstract base class for all data processors.

    This class provides a shared foundation for processing raw product data.
    It defines a standard schema (`FINAL_COLUMNS`), common helper methods for
    parsing prices and quantities, and an abstract interface that concrete

    subclasses must implement for market-specific logic like category and
    store location extraction.
    """

    # Define the final, ordered columns for the output after processing
    FINAL_COLUMNS = [
        "product_name",
        "current_price",
        "price_per_unit",
        "unit",
        "category",
        "discount_percentage",
        "store_location",
    ]

    UNIT_TYPE_MAP = (
        {  # This is a mapping of the unit types to the unit column in the output
            "volume": "l",
            "weight": "kg",
            "pieces": "piece",
        }
    )

    MEASUREMENT_PATTERNS = {  # This is a mapping of the measurement patterns to the standardized units
        "volume": {
            "units": ["МЛ", "Л", "ЛТ", "ЛИТАР", "ЛИТРИ", "ML", "L", "LT"],
            "pattern": r"(\d+(?:\.\d+)?)\s*(МЛ|Л|ЛТ|ЛИТАР|ЛИТРИ|ML|L|LT)",
            "multipliers": {
                "МЛ": 1,
                "Л": 1000,
                "ЛТ": 1000,
                "ЛИТАР": 1000,
                "ЛИТРИ": 1000,
                "ML": 1,
                "L": 1000,
                "LT": 1000,
            },
        },
        "weight": {
            "units": [
                "Г",
                "ГР",
                "КГ",
                "ГРАМ",
                "КИЛОГРАМ",
                "ГРАМОВИ",
                "КИЛОГРАМИ",
                "КГР",
                "G",
                "GR",
                "KG",
            ],
            "pattern": r"(\d+(?:\.\d+)?)\s*(Г|ГР|КГ|ГРАМ|КИЛОГРАМ|ГРАМОВИ|КИЛОГРАМИ|КГР|G|GR|KG)",
            "multipliers": {
                "Г": 1,
                "ГР": 1,
                "КГ": 1000,
                "ГРАМ": 1,
                "КИЛОГРАМ": 1000,
                "ГРАМОВИ": 1,
                "КИЛОГРАМИ": 1000,
                "КГР": 1000,
                "G": 1,
                "GR": 1,
                "KG": 1000,
            },
        },
        "pieces": {
            "units": [
                "КОМ",
                "ПАР",
                "БРОЈ",
                "ПАРЧЕ",
                "PAR",
                "PARCE",
                "PARCHE",
                "PCS",
                "PC",
            ],
            "pattern": r"(\d+)\s*(КОМ|ПАР|БРОЈ|ПАРЧЕ|PAR|PARCE|PARCHE|PCS|PC)",
            "multipliers": {
                "КОМ": 1,
                "ПАР": 1,
                "БРОЈ": 1,
                "ПАРЧЕ": 1,
                "PAR": 1,
                "PARCE": 1,
                "PARCHE": 1,
                "PCS": 1,
                "PC": 1,
            },
        },
    }

    # --- Public API ---

    def create_product_data(
        self,
        product_name: str,
        current_price: str,
        regular_price: str,
        description: str,
        price_per_unit: str,
        availability: str,
        store_name: str,
    ) -> Dict[str, Any]:
        """Creates a standardized product data dictionary from raw string inputs.

        This method acts as a pipeline, taking all raw data fields for a single
        product, calling various helper methods to clean, parse, and calculate
        values, and finally assembling a structured dictionary with a consistent
        schema defined by `FINAL_COLUMNS`.

        Args:
            product_name: The raw name of the product.
            current_price: The current selling price as a string.
            regular_price: The original (non-discounted) price as a string.
            description: The raw description or category string.
            price_per_unit: The price per standard unit (e.g., "per kg").
            availability: The availability status (e.g., "ДА", "In Stock").
            store_name: The raw name of the store or market branch.

        Returns:
            A dictionary containing cleaned and standardized product data.
        """

        # --- Step 1: Extract all data efficiently ---
        current_price_val = self._extract_price(current_price)
        regular_price_val = self._extract_price(regular_price)

        # Extract measurement data ONCE
        name_data = self._extract_quantity_and_unit_from_product_name(product_name)
        ppu_data = self._extract_quantity_and_unit_from_price_per_unit(
            price_per_unit, current_price
        )

        # --- Step 2: Establish a single source of truth for measurements ---
        if name_data.get("unit_type"):
            measurement_data = name_data
        elif ppu_data.get("unit_type"):
            measurement_data = ppu_data
        else:
            # Default fallback for items with no discernible unit (e.g., single piece)
            measurement_data = {
                "quantity": 1.0,
                "unit": "PIECE",
                "unit_type": "pieces",
                "standard_quantity": 1.0,
            }

        # --- Step 3: Perform calculations using the extracted data ---

        # Calculate discount
        discount = 0.0
        if (
            regular_price_val
            and current_price_val
            and regular_price_val > 0
            and current_price_val < regular_price_val
        ):
            discount = round(
                ((regular_price_val - current_price_val) / regular_price_val) * 100, 2
            )

        # Calculate standardized price per unit
        price_per_unit_val = None
        standard_quantity = measurement_data.get("standard_quantity")
        if current_price_val and standard_quantity and standard_quantity > 0:
            price_per_unit_val = round(current_price_val / standard_quantity, 2)

        # --- Step 4: Assemble the final, clean dictionary ---

        # Map the internal 'unit_type' to the desired final 'unit' name
        unit_type = measurement_data.get("unit_type")
        unit_name = self.UNIT_TYPE_MAP.get(unit_type)

        result = {
            "product_name": self._process_product_name(product_name),
            "current_price": current_price_val,
            "price_per_unit": price_per_unit_val,
            "unit": unit_name,
            "category": self._get_category(description, product_name),
            "discount_percentage": discount,
            "store_location": self._create_store_location(store_name),
        }

        return result

    def generate_clean_csv(self, input_file: str, output_file: str):
        """Processes a raw data file and saves the result to a clean CSV.

        This method orchestrates the processing of an entire market data file by
        calling the market-specific `process_market_data` implementation and
        then saving the resulting DataFrame to a specified CSV file.

        Args:
            input_file: The path to the input file containing raw data.
            output_file: The path where the clean CSV will be saved.
        """
        self.logger.info(f"Starting processing for {input_file}...")

        # Process the data using the market-specific implementation
        clean_df = self.process_market_data(input_file)

        # Save the final DataFrame
        self.save_df_to_csv(clean_df, output_file)

        self.logger.info(f"Processing complete. Clean data saved to {output_file}.")

    def save_df_to_csv(self, df: pd.DataFrame, file_path: str):
        """Saves a pandas DataFrame to a CSV file.

        Ensures the output directory exists and saves the DataFrame using
        'utf-8-sig' encoding to handle special characters correctly,
        particularly for Excel compatibility.

        Args:
            df: The pandas DataFrame to save.
            file_path: The full path for the output CSV file.
        """
        if df.empty:
            self.logger.warning("DataFrame is empty. Nothing to save.")
            return

        try:
            output_dir = os.path.dirname(file_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            self.logger.info(f"Successfully saved {len(df)} records to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save DataFrame to {file_path}: {e}")

    # --- Abstract Methods (to be implemented by subclasses) ---

    @abstractmethod
    def process_market_data(self, file_path: str) -> pd.DataFrame:
        """Process market-specific data from a file and return a cleaned DataFrame.

        This abstract method must be implemented by subclasses to handle the specific
        data format and processing requirements of each market. The implementation
        should read the input file, apply market-specific transformations, and return
        a standardized DataFrame with the expected schema.

        Args:
            file_path (str): Path to the input file containing raw market data.

        Returns:
            pd.DataFrame: Cleaned and standardized DataFrame with columns matching
                         the expected schema (product_name, price, unit, category,
                         discount_percentage, store_location).
        """
        pass

    @abstractmethod
    def _get_category(self, description: str, product_name: str) -> Optional[str]:
        """Extract and return the product category based on description and product name.

        This abstract method must be implemented by subclasses to determine the appropriate
        category for a product based on its description and name. The implementation should
        use market-specific logic, keyword matching, or other categorization strategies
        to assign products to meaningful categories.

        Args:
            description (str): Product description text that may contain category information.
            product_name (str): The name of the product that may contain category clues.

        Returns:
            Optional[str]: The determined category name, or None if no category can be determined.
        """
        pass

    @abstractmethod
    def _create_store_location(self, store_name: str) -> str:
        """Create a standardized store location string from the store name.

        This abstract method must be implemented by subclasses to create a consistent
        store location format based on the market's store naming conventions. The
        implementation should handle market-specific store name patterns and return
        a standardized location string.

        Args:
            store_name (str): The raw store name from the market data that needs
                             to be converted to a standardized location format.

        Returns:
            str: A standardized store location string that follows the market's
                 location naming conventions.
        """
        pass

    # --- Protected Helper Methods ---

    def _process_product_name(self, product_name: str) -> str:
        """Cleans and standardizes a product name string.

        Operations include converting to uppercase, removing extra whitespace,
        and stripping leading/trailing spaces.

        Args:
            product_name: The raw product name to be processed.

        Returns:
            The processed product name, or an empty string if input is invalid.
        """
        if not product_name:
            return ""

        # To uppercase and strip whitespace
        processed_name = re.sub(r"\s+", " ", product_name).strip().upper()

        return processed_name

    def _extract_quantity_and_unit_from_product_name(
        self, product_name: str
    ) -> Dict[str, Any]:
        """Parses a product name to find quantity and unit information.

        It searches the product name for patterns defined in `MEASUREMENT_PATTERNS`
        (e.g., "500Г", "1.5Л"). To handle variations like "1,5Л", it works on a
        sanitized copy of the name.

        Args:
            product_name: The raw product name string.

        Returns:
            A dictionary containing:
                - 'quantity' (float): The detected numeric quantity.
                - 'unit' (str): The detected unit string (e.g., 'Г', 'Л').
                - 'unit_type' (str): The general category ('weight', 'volume').
                - 'standard_quantity' (float): Quantity converted to a base
                  unit (e.g., grams to kilograms, milliliters to liters).
            Returns a dictionary with None values if no pattern is matched.
        """
        if not product_name or not isinstance(product_name, str):
            return {"quantity": None, "unit": None, "unit_type": None}

        # Create a sanitized version for parsing, leaving the original name untouched.
        # 1. Replace commas with periods for decimal conversion.
        # 2. Replace slashes with spaces to separate numbers (e.g., "1/1KG" -> "1 1KG").
        sanitized_name = product_name.replace(",", ".").replace("/", " ")

        for measurement_type, config in self.MEASUREMENT_PATTERNS.items():
            match = re.search(config["pattern"], sanitized_name, re.IGNORECASE)
            if match:
                quantity = float(match.group(1))
                unit = match.group(2).upper()
                standard_quantity = self._convert_to_standard(
                    quantity, unit, measurement_type
                )
                return {
                    "quantity": quantity,
                    "unit": unit,
                    "unit_type": measurement_type,
                    "standard_quantity": standard_quantity,
                }

        return {"quantity": None, "unit": None, "unit_type": None}

    def _extract_quantity_and_unit_from_price_per_unit(
        self, price_per_unit: str, current_price: str
    ) -> Dict[str, Any]:
        """Parses a 'price per unit' string to find quantity and unit.

        This function is similar to `_extract_quantity_and_unit_from_product_name`
        but operates on the price-per-unit field. It includes a check to avoid
        misinterpreting cases where the 'price per unit' field simply repeats
        the main price.

        Args:
            price_per_unit: The raw price-per-unit string (e.g., "150 ДЕН / КГ").
            current_price: The main price of the product, used for comparison.

        Returns:
            A dictionary with 'quantity', 'unit', 'unit_type', and
            'standard_quantity', or None values if no pattern is matched.
        """
        if not price_per_unit or not isinstance(price_per_unit, str):
            return {"quantity": None, "unit": None, "unit_type": None}

        current_price_clean = self._extract_price(current_price)
        ppu_price = self._extract_price_per_unit_value(price_per_unit)

        if (
            current_price_clean
            and ppu_price
            and abs(current_price_clean - ppu_price) < 0.01
        ):
            return {"quantity": None, "unit": None, "unit_type": None}

        for measurement_type, config in self.MEASUREMENT_PATTERNS.items():
            match = re.search(config["pattern"], price_per_unit, re.IGNORECASE)
            if match:
                quantity = float(match.group(1))
                unit = match.group(2).upper()
                standard_quantity = self._convert_to_standard(
                    quantity, unit, measurement_type
                )
                return {
                    "quantity": quantity,
                    "unit": unit,
                    "unit_type": measurement_type,
                    "standard_quantity": standard_quantity,
                }

        return {"quantity": None, "unit": None, "unit_type": None}

    def _extract_price(self, price_str: str) -> Optional[float]:
        """Extracts a float value from a string representing a price.

        Handles various formats, removing currency symbols and non-numeric
        characters. It correctly interprets both '.' and ',' as potential
        decimal separators.

        Args:
            price_str: The raw price string (e.g., "1.299,99 ДЕН").

        Returns:
            The cleaned price as a float, or None if conversion fails.
        """
        if not price_str or not isinstance(price_str, str):
            return None
        price_clean = re.sub(r"[^\d.,]", "", price_str)
        if "," in price_clean and "." in price_clean:
            price_clean = price_clean.replace(",", "")
        elif "," in price_clean:
            price_clean = price_clean.replace(",", ".")
        try:
            return float(price_clean)
        except ValueError:
            return None

    def _extract_price_per_unit_value(self, ppu_str: str) -> Optional[float]:
        """Extracts a numeric value from a complex price-per-unit string.

        This function is designed to parse strings like "150.00 ДЕН / КГ" and
        extract the numeric price part. It standardizes the value based on the
        detected unit to a base unit (e.g., price per gram to price per kilogram).

        Args:
            ppu_str: The raw price-per-unit string.

        Returns:
            The calculated price per standard unit as a float, or None if
            parsing fails.
        """
        # if None, calculate it from product name. use extract quantity and unit from product name function
        # and standardize it, then use current price to calculate price per unit (standardized)
        if not ppu_str or not isinstance(ppu_str, str):
            return None

        for measurement_type, config in self.MEASUREMENT_PATTERNS.items():
            match = re.search(
                r"(\d+(?:\.\d+)?)\s*ДЕН\s*/\s*(\w+)", ppu_str.upper(), re.IGNORECASE
            )
            # match = re.search(config['pattern'], ppu_str.upper(), re.IGNORECASE)
            if match:
                try:
                    price_value = float(match.group(1))
                    unit = match.group(2).upper()
                    if unit in config["multipliers"]:
                        multiplier = config["multipliers"][unit]
                        return price_value * multiplier / 1000.0
                    else:
                        return price_value
                except ValueError:
                    continue

        patterns = [
            r"(\d+(?:\.\d+)?)\s*ДЕН",
            r"(\d+(?:\.\d+)?)\s*ДЕНАР",
            r"(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, ppu_str.upper(), re.IGNORECASE)
            if match:
                try:
                    return (
                        float(match.group(2))
                        if len(match.groups()) == 2
                        else float(match.group(1))
                    )
                except ValueError:
                    continue
        return None

    def _convert_to_standard(self, quantity: float, unit: str, unit_type: str) -> float:
        """Converts a measurement to a standard base unit.

        For 'volume' and 'weight', the standard base unit is 1000 (for liters
        and kilograms, respectively). For 'pieces', it is 1.

        Example:
            _convert_to_standard(500, 'ГР', 'weight') -> 0.5 (kg)
            _convert_to_standard(2, 'Л', 'volume') -> 2.0 (l)

        Args:
            quantity: The numeric value of the measurement.
            unit: The unit string (e.g., 'ГР', 'Л', 'КОМ').
            unit_type: The type of measurement ('weight', 'volume', 'pieces').

        Returns:
            The quantity converted to the standard base unit as a float.
        """
        multipliers = self.MEASUREMENT_PATTERNS[unit_type]["multipliers"]
        if unit not in multipliers:
            return quantity
        base_quantity = quantity * multipliers[unit]
        return (
            base_quantity / 1000.0
            if unit_type in ["volume", "weight"]
            else base_quantity
        )

    def _extract_availability(self, availability: str) -> Optional[bool]:
        """Converts a string representation of availability into a boolean.

        Handles various localized and common terms for "available" and
        "unavailable".

        Args:
            availability: The raw availability string (e.g., "ДА", "No").

        Returns:
            True if available, False if unavailable, or None if the string
            is not recognized or empty.
        """
        if not availability or not isinstance(availability, str):
            return None
        availability_upper = availability.upper().strip()
        available_indicators = [
            "DA",
            "YES",
            "TRUE",
            "1",
            "AVAILABLE",
            "НА РАСПОЛАГАЊE",
            "ДА",
        ]
        unavailable_indicators = ["NE", "NO", "FALSE", "0", "UNAVAILABLE", "НЕ", "НЕМА"]
        if availability_upper in available_indicators:
            return True
        elif availability_upper in unavailable_indicators:
            return False
        return None
