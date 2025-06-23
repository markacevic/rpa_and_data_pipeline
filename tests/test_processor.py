"""
Tests for the data processing module.

This module contains a suite of tests for the `VeroDataProcessor` class.
It uses pytest fixtures to create sample data files and verifies that the
processor correctly processes the data into a structured format.
"""

import pandas as pd
import pytest
from src.processors.vero_data_processor import VeroDataProcessor


@pytest.fixture
def raw_data_file(tmp_path):
    """Creates a temporary raw data JSON file for testing.

    This pytest fixture generates a temporary JSON file containing a list of
    raw product data. This file is used as input for the data processor tests.

    Args:
        tmp_path: The pytest `tmp_path` fixture, which provides a temporary
            directory unique to the test invocation.

    Returns:
        pathlib.Path: The path to the created temporary JSON file.
    """
    raw_data = [
        {
            "назив_на_стока": "ЦЕРАЛИИ ТРИКС 300ГР",
            "продажна_цена\n(со_ддв)": "209",
            "единечна_цена": "697 ден/кг",
            "достапност_во\nпродажен_објект": "Да",
            "опис_на_стока": "ЧАЕВИ,КАКАО,КОРНФЛЕКС - ВИТ.ХРАНА-КОРНФЛЕКС,ЖИТАРИЦИ",
            "редовна_цена\n(со_ддв)": "303",
            "цена_со_попуст": "209",
            "попуст_(%)": "31 %",
            "вид_на_продажно_потикнување": "Промотивна цена",
            "времетраење_на_промоција_или_попуст": "11/06/2025 - 24/06/2025",
            "market_code": "104",
            "market_name": "ВЕРО 7",
            "scraped_at": "2025-06-22 09:55:39",
        },
        {
            "назив_на_стока": "ИНСТАНТ НАПИТОК НЕСКВИК 400Г КЕСА",
            "продажна_цена\n(со_ддв)": "239",
            "единечна_цена": "598 ден/кг",
            "достапност_во\nпродажен_објект": "Да",
            "опис_на_стока": "ЧАЕВИ,КАКАО,КОРНФЛЕКС - КАКАО",
            "редовна_цена\n(со_ддв)": "299",
            "цена_со_попуст": "239",
            "попуст_(%)": "20 %",
            "вид_на_продажно_потикнување": "Промотивна цена",
            "времетраење_на_промоција_или_попуст": "11/06/2025 - 24/06/2025",
            "market_code": "104",
            "market_name": "ВЕРО 7",
            "scraped_at": "2025-06-22 09:55:39",
        },
        {
            "назив_на_стока": "НАПИТОК ЦЕДЕВИТА ИНСТАНТ АНАНАС И МАНГО 455ГР",
            "продажна_цена\n(со_ддв)": "155",
            "единечна_цена": "341 ден/кг",
            "достапност_во\nпродажен_објект": "Да",
            "опис_на_стока": "ЧАЕВИ,КАКАО,КОРНФЛЕКС-ИНСТАНТ НАПИТОЦИ",
            "редовна_цена\n(со_ддв)": "205",
            "цена_со_попуст": "155",
            "попуст_(%)": "24 %",
            "вид_на_продажно_потикнување": "Промотивна цена",
            "времетраење_на_промоција_или_попуст": "11/06/2025 - 24/06/2025",
            "market_code": "104",
            "market_name": "ВЕРО 7",
            "scraped_at": "2025-06-22 09:55:39",
        },
    ]
    fpath = tmp_path / "raw.json"
    pd.DataFrame(raw_data).to_json(fpath, orient="records")
    return fpath


def test_process_market_data(raw_data_file):
    """Tests the functionality of the VeroDataProcessor.

    This test checks the following aspects of the `process_market_data` method:
    1.  That the output is a pandas DataFrame.
    2.  That the number of processed records is correct.
    3.  The accuracy of key data points (name, price, category, discount) for
        each processed product.
    4.  That the final DataFrame schema (column names and data types) matches
        the expected structure.

    Args:
        raw_data_file (pathlib.Path): The path to the temporary raw data file,
            provided by the `raw_data_file` fixture.
    """
    processor = VeroDataProcessor()
    df = processor.process_market_data(raw_data_file)

    # Check that the result is a pandas DataFrame
    assert isinstance(df, pd.DataFrame)

    # --- Data Content Validation ---

    # There should be 3 products from the raw data
    assert len(df) == 3

    # Check the first product (ЦЕРАЛИИ ТРИКС 300ГР)
    assert df.loc[0, "product_name"] == "ЦЕРАЛИИ ТРИКС 300ГР"
    assert df.loc[0, "current_price"] == 209.0
    assert (
        df.loc[0, "category"] == "ЧАЕВИ,КАКАО,КОРНФЛЕКС - ВИТ.ХРАНА-КОРНФЛЕКС,ЖИТАРИЦИ"
    )
    assert df.loc[0, "discount_percentage"] == 31.02

    # Check the second product (ИНСТАНТ НАПИТОК НЕСКВИК 400Г КЕСА)
    assert df.loc[1, "product_name"] == "ИНСТАНТ НАПИТОК НЕСКВИК 400Г КЕСА"
    assert df.loc[1, "current_price"] == 239.0
    assert df.loc[1, "category"] == "ЧАЕВИ,КАКАО,КОРНФЛЕКС - КАКАО"
    assert df.loc[1, "discount_percentage"] == 20.07

    # Check the third product (НАПИТОК ЦЕДЕВИТА ИНСТАНТ АНАНАС И МАНГО 455ГР)
    assert df.loc[2, "product_name"] == "НАПИТОК ЦЕДЕВИТА ИНСТАНТ АНАНАС И МАНГО 455ГР"
    assert df.loc[2, "current_price"] == 155.0
    assert df.loc[2, "category"] == "ЧАЕВИ,КАКАО,КОРНФЛЕКС-ИНСТАНТ НАПИТОЦИ"
    assert df.loc[2, "discount_percentage"] == 24.39

    # --- Schema and Data Type Validation ---

    # Define the expected schema (column names and their dtypes)
    expected_schema = {
        "product_name": "object",
        "current_price": "float64",
        "price_per_unit": "float64",
        "unit": "object",
        "category": "object",
        "discount_percentage": "float64",
        "store_location": "object",
    }

    # Check that the columns are exactly as expected
    assert set(df.columns) == set(expected_schema.keys())

    # Check the data type of each column
    for col, expected_dtype in expected_schema.items():
        assert (
            df[col].dtype == expected_dtype
        ), f"Column '{col}' has dtype {df[col].dtype}, expected {expected_dtype}"
