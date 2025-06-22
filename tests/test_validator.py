import pandas as pd
from src.validators.data_validator import DataValidator

def test_validate_data():
    raw_data = pd.DataFrame([
        {"product_name": "Milk 1L", "current_price": 50.0, "price_per_unit": 50.0, "unit": "l", "category": "Dairy", "discount_percentage": 0.0, "store_location": "Vero Market Centar"},
        {"product_name": "", "current_price": None, "price_per_unit": None, "unit": "", "category": "", "discount_percentage": None, "store_location": ""},
        {"product_name": "Cheese 500g", "current_price": -10.0, "price_per_unit": -20.0, "unit": "kg", "category": "Dairy", "discount_percentage": 0.0, "store_location": "Vero Market Centar"}
    ])

    validator = DataValidator()
    validated = validator.validate(raw_data)

    assert isinstance(validated, pd.DataFrame)
    assert len(validated) == 1  # Only the first row should pass