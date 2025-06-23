# -*- coding: utf-8 -*-
import pandas as pd
import logging
import json
import os
from jsonschema import validate, ValidationError


class DataValidator:
    """Validates processed data and generates a quality report.

    This class is responsible for validating a DataFrame of processed product
    data against a predefined JSON schema. It identifies and logs any
    schema violations, removes duplicate entries, and generates a detailed
    JSON report summarizing the validation results.

    Attributes:
        logger: A configured logger for the class.
        schema: The JSON schema used for validation.
        validation_errors: A list to store details of validation failures.
    """

    def __init__(self):
        """Initializes the DataValidator instance."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.schema = self._define_schema()
        self.validation_errors = []

    def _define_schema(self) -> dict:
        """Defines the JSON schema for a single valid processed product record.

        This schema enforces data types, required fields, and value constraints
        for each product record to ensure data quality and consistency.

        Returns:
            dict: A dictionary representing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "minLength": 1},
                "current_price": {"type": "number", "exclusiveMinimum": 0},
                "price_per_unit": {"type": ["number", "null"], "exclusiveMinimum": 0},
                "unit": {"type": "string", "enum": ["kg", "l", "piece"]},
                "category": {"type": "string"},
                "discount_percentage": {"type": "number", "minimum": 0, "maximum": 100},
                "store_location": {"type": "string", "minLength": 1},
            },
            "required": [
                "product_name",
                "current_price",
                "price_per_unit",
                "unit",
                "category",
                "discount_percentage",
                "store_location",
            ],
        }

    def validate(self, df: pd.DataFrame, market_name: str) -> pd.DataFrame:
        """Validates a DataFrame against the schema and removes duplicates.

        This method iterates through each row of the input DataFrame, validates
        it against the JSON schema, and collects any errors. It then generates
        a validation report, removes duplicate records, and returns a new
        DataFrame containing only the valid, unique data.

        Args:
            df (pd.DataFrame): The DataFrame containing processed product data.
            market_name (str): The name of the market, used for the report filename.

        Returns:
            pd.DataFrame: A cleaned DataFrame containing only the records that
                passed both schema validation and duplicate checks.
        """
        self.logger.info(
            f"Starting validation for {len(df)} records from '{market_name}'..."
        )
        self.validation_errors = []  # Reset errors for each run

        # Convert DataFrame to a list of records for validation
        records = df.to_dict("records")
        valid_records = []

        for i, record in enumerate(records):
            try:
                validate(instance=record, schema=self.schema)
                valid_records.append(record)
            except ValidationError as e:
                error_details = {
                    "record_index": i,
                    "product_name": record.get("product_name", "N/A"),
                    "error_message": e.message,
                    "validator": e.validator,
                    "path": list(e.path),
                }
                self.validation_errors.append(error_details)

        # Create a new DataFrame from only the valid records
        validated_df = pd.DataFrame(valid_records)

        # Generate the report before handling duplicates
        self._generate_report(original_count=len(df), market_name=market_name)

        # Perform duplicate check after schema validation

        if not validated_df.empty:
            initial_count = len(validated_df)
            validated_df.drop_duplicates(
                subset=["product_name", "store_location"], keep="first", inplace=True
            )
            dropped_duplicates = initial_count - len(validated_df)
            if dropped_duplicates > 0:
                self.logger.info(f"Dropped {dropped_duplicates} duplicate records.")

        final_count = len(validated_df)
        self.logger.info(
            f"Validation complete. {final_count} records passed all checks."
        )
        return validated_df

    def _generate_report(self, original_count: int, market_name: str) -> None:
        """Generates and saves a JSON report summarizing validation results.

        The report includes a summary of processed, passed, and failed
        records, along with a detailed list of all validation errors that
        occurred.

        Args:
            original_count (int): The total number of records in the original DataFrame.
            market_name (str): The name of the market, used for naming the report file.
        """
        report = {
            "validation_summary": {
                "total_records_processed": original_count,
                "records_passed_schema": original_count - len(self.validation_errors),
                "records_failed_schema": len(self.validation_errors),
            },
            "validation_errors": self.validation_errors,
        }

        # Use the market_name to create a dynamic report filename
        report_filename = f"{market_name.lower()}_validation_report.json"
        report_path = os.path.join("outputs", "reports", report_filename)

        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Validation report saved to {report_path}")
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")
