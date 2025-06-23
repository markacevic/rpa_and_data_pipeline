# -*- coding: utf-8 -*-
"""
Main runner script for the web scraping project.
This script uses a factory to get the correct scraper for a given market
and then runs the scraping process.
"""
import logging
import argparse
from src.scrapers.factory import get_market_scraper
from src.processors import get_data_processor
from src.validators.data_validator import DataValidator
from src.reporting.analytics import generate_summary_analytics
from config.settings import MARKET_CONFIGS # Import the configurations
import pandas as pd
import os

def setup_logging():
    """Sets up basic logging for the script.

    This function configures the root logger to use the INFO level and a
    standard format for logging messages.
    """
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """Parses command-line arguments and runs the specified market scraper.

    This function handles argument parsing, initializes the appropriate scraper
    based on the provided market, and orchestrates the scraping, processing,
    and validation workflow.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Run a market scraper.")
    parser.add_argument("market", type=str, help="The name of the market to scrape (e.g., 'Vero', 'Tinex').")
    parser.add_argument("--browser", type=str, default="chrome", choices=['edge', 'chrome', 'firefox'], help="The browser to use for scraping.")
    parser.add_argument("--page-limit", type=int, default=None, help="The maximum number of products to scrape per page.")
    parser.add_argument("--total-limit", type=int, default=None, help="The maximum total number of products to scrape across all pages.")
    parser.add_argument("--no-headless", action="store_true", help="Run the browser in non-headless mode (visible).")
    args = parser.parse_args()

    # --- Load Market Configuration ---
    market_key = args.market.lower()
    config = MARKET_CONFIGS.get(market_key)
    if not config:
        logging.error(f"Configuration for market '{args.market}' not found in settings.py.")
        return

    setup_logging()
    logging.info(f"Starting scraper for '{args.market}' with a limit of {args.total_limit} products.")
    
    try:
        logging.info(f"Initializing scraper for '{args.market}'...")
        scraper = get_market_scraper(
            market_name=market_key,
            base_url=config['base_url'],
            browser=args.browser,
            headless=not args.no_headless,
            per_page_limit=args.page_limit,
            total_limit=args.total_limit
        )
        
        output_files = scraper.scrape()

        if not output_files:
            logging.warning(f"No data was scraped for {args.market}. Skipping processing.")
            return

        # --- Data Processing Step ---
        logging.info(f"Starting data processing for '{args.market}'...")
        processor = get_data_processor(args.market)
        
        all_processed_data = []
        for raw_file_path in output_files:
            processed_df = processor.process_market_data(raw_file_path)
            if not processed_df.empty:
                all_processed_data.append(processed_df)

        if not all_processed_data:
            logging.warning(f"No processable product data found for {args.market}. No report generated.")
            return

        final_df = pd.concat(all_processed_data, ignore_index=True)
        
        # --- Data Validation Step ---
        logging.info("Starting data validation...")
        validator = DataValidator()
        validated_df = validator.validate(final_df, market_name=market_key)

        if validated_df.empty:
            logging.warning("No data remained after validation. No reports will be generated.")
            return

        # --- Generate Analytics Report Step ---
        logging.info("Generating summary analytics report...")
        analytics_report_path = os.path.join('outputs', 'reports', f"{args.market.lower()}_summary_analytics_report.json")
        generate_summary_analytics(validated_df, analytics_report_path)

        # --- Save Final Validated Data ---
        output_dir = 'outputs'
        os.makedirs(output_dir, exist_ok=True)
        
        output_csv_path = os.path.join(output_dir, f"{args.market.lower()}_processed_data.csv")
        
        validated_df.to_csv(output_csv_path, index=False, encoding='utf-8')
        logging.info(f"Successfully processed and saved {len(validated_df)} validated records to {output_csv_path}")

    except ValueError as e:
        logging.error(e)
    except Exception as e:
        logging.error(f"An unexpected error occurred in main: {e}", exc_info=True)

if __name__ == "__main__":
    main() 