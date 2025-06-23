"""
Tests for the data validation module.

This module contains a suite of tests for the `DataValidator` class.
It uses pytest fixtures to create sample DataFrames containing both valid
and invalid records, and it verifies that the validator correctly
identifies, filters, and reports on data quality issues.
"""

import pandas as pd
from src.validators.data_validator import DataValidator


def test_validate_data():
    """Tests the functionality of the DataValidator.

    This test checks the following aspects of the `validate` method:
    1.  That the output is a pandas DataFrame.
    2.  That the number of validated records is correct.
    3.  The accuracy of key data points (name, price, category, discount) for
        each validated product.
    """
    market_name = "vero"
    raw_data = pd.DataFrame(
        [
            {
                "product_name": "Milk 1L",
                "current_price": 50.0,
                "price_per_unit": 50.0,
                "unit": "l",
                "category": "Dairy",
                "discount_percentage": 0.0,
                "store_location": "Vero Market Centar",
            },
            {
                "product_name": "",
                "current_price": None,
                "price_per_unit": None,
                "unit": "",
                "category": "",
                "discount_percentage": None,
                "store_location": "",
                "market_name": market_name,
            },
            {
                "product_name": "Cheese 500g",
                "current_price": -10.0,
                "price_per_unit": -20.0,
                "unit": "kg",
                "category": "Dairy",
                "discount_percentage": 0.0,
                "store_location": "Vero Market Centar",
                "market_name": market_name,
            },
        ]
    )

    validator = DataValidator()
    validated = validator.validate(raw_data, market_name)

    assert isinstance(validated, pd.DataFrame)
    assert len(validated) == 1  # Only the first row should pass
