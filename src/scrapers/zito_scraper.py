# -*- coding: utf-8 -*-
from .base_market_scraper import BaseMarketScraper
from typing import Optional

class ZitoScraper(BaseMarketScraper):
    """
    A scraper for the Zito supermarket website.
    This class inherits all its scraping logic from the BaseMarketScraper.
    """
    def __init__(self, base_url: str, browser: str = 'chrome', per_page_limit: Optional[int] = None, total_limit: Optional[int] = None, headless: bool = True):
        super().__init__(
            base_url=base_url,
            market_name="Zito",
            browser=browser,
            per_page_limit=per_page_limit,
            total_limit=total_limit,
            headless=headless
        )
    # No Zito-specific logic is needed here for now, as the base class handles everything.

if __name__ == '__main__':
    import logging

    # This block allows for direct testing of the ZitoScraper.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # --- Configuration for the test run ---
    ZITO_BASE_URL = "https://zito.proverkanaceni.mk/index.php"
    TEST_PRODUCT_LIMIT = 10 
    IS_HEADLESS = False

    logging.info(f"--- Starting direct test run for ZitoScraper (limit: {TEST_PRODUCT_LIMIT} products) ---")
    
    try:
        with ZitoScraper(
            base_url=ZITO_BASE_URL,
            total_limit=TEST_PRODUCT_LIMIT,
            headless=IS_HEADLESS
        ) as test_scraper:
            output_files = test_scraper.scrape()
            
            if output_files:
                logging.info(f"ZitoScraper direct test run finished successfully. Data saved to: {output_files}")
            else:
                logging.warning("ZitoScraper test run completed, but no data was saved.")
            
    except Exception as e:
        logging.error(f"An error occurred during the ZitoScraper test run: {e}", exc_info=True)

    