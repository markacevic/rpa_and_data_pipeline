# -*- coding: utf-8 -*-
from .base_market_scraper import BaseMarketScraper
from typing import Optional

class TinexScraper(BaseMarketScraper):
    """
    A scraper for the Tinex supermarket website.
    This class inherits all its scraping logic from the BaseMarketScraper.
    """
    def __init__(self, base_url: str, browser: str = 'chrome', per_page_limit: Optional[int] = None, total_limit: Optional[int] = None, headless: bool = True):
        super().__init__(
            base_url=base_url,
            market_name="Tinex",
            browser=browser,
            per_page_limit=per_page_limit,
            total_limit=total_limit,
            headless=headless
        )
        # No Tinex-specific logic is needed here for now, as the base class handles everything.

if __name__ == '__main__':
    import logging

    # This block allows for direct testing of the TinexScraper.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # --- Configuration for the test run ---
    TINEX_BASE_URL = "https://ceni.tinex.mk:442/index.php"
    TEST_PRODUCT_LIMIT = 50 
    IS_HEADLESS = False

    logging.info(f"--- Starting direct test run for TinexScraper (limit: {TEST_PRODUCT_LIMIT} products) ---")
    
    try:
        with TinexScraper(
            base_url=TINEX_BASE_URL,
            total_limit=TEST_PRODUCT_LIMIT,
            headless=IS_HEADLESS
        ) as test_scraper:
            output_files = test_scraper.scrape()
            
            if output_files:
                logging.info(f"TinexScraper direct test run finished successfully. Data saved to: {output_files}")
            else:
                logging.warning("TinexScraper test run completed, but no data was saved.")
            
    except Exception as e:
        logging.error(f"An error occurred during the TinexScraper test run: {e}", exc_info=True)
