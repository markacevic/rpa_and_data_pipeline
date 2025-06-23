# -*- coding: utf-8 -*-
"""Module for generating summary analytics from processed data.

This module provides functions to calculate key statistics from the cleaned
supermarket data, such as price distributions and discount information,
and saves the results as a JSON report.
"""
import logging
import json
import os
import pandas as pd


def generate_summary_analytics(df: pd.DataFrame, output_path: str):
    """
    Generates a summary analytics report from the validated DataFrame
    and saves it as a JSON file.

    This function takes a cleaned DataFrame of product data and computes
    various analytics, including:
    - Total number of products and number on discount.
    - Analytics per product category (count, average price).
    - A summary of the top 10 most and least expensive products.

    The resulting analytics are saved to a specified JSON file.

    Args:
        df: The validated and cleaned pandas DataFrame. Must include at
            least 'current_price', 'discount_percentage', and 'category'.
        output_path: The file path where the JSON report will be saved.
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Generating summary analytics for {len(df)} records...")

    if df.empty:
        logger.warning("Input DataFrame is empty, skipping analytics generation.")
        return

    try:
        # Basic stats
        total_products = int(df.shape[0])
        products_on_discount = int(df[df["discount_percentage"] > 0].shape[0])

        # Per-category analytics
        category_analytics = {}
        if "category" in df.columns and not df["category"].isnull().all():
            category_group = df.groupby("category")
            category_analytics = {
                "products_per_category": category_group.size().to_dict(),
                "average_price_per_category": category_group["current_price"]
                .mean()
                .round(2)
                .to_dict(),
            }
        else:
            logger.warning("No category data available for analytics.")

        # Top 10 products
        df_sorted_price = df.sort_values(by="current_price", ascending=False)
        top_10_expensive = df_sorted_price.head(10)[
            ["product_name", "current_price"]
        ].to_dict("records")
        top_10_cheapest = (
            df_sorted_price.tail(10)
            .sort_values(by="current_price", ascending=True)[
                ["product_name", "current_price"]
            ]
            .to_dict("records")
        )

        report = {
            "report_generated_at": pd.Timestamp.now().isoformat(),
            "total_products": total_products,
            "products_on_discount": products_on_discount,
            "discount_ratio": (
                round(products_on_discount / total_products, 2)
                if total_products > 0
                else 0
            ),
            **category_analytics,
            "top_10_expensive_products": top_10_expensive,
            "top__10_cheapest_products": top_10_cheapest,
        }

        # Save the report
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=4)

        logger.info(
            f"Successfully generated and saved analytics report to {output_path}"
        )

    except Exception as e:
        logger.error(f"Failed to generate analytics report: {e}", exc_info=True)
        raise
