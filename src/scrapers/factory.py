from .vero_scraper import VeroScraper
from .tinex_scraper import TinexScraper
from .zito_scraper import ZitoScraper
from .stokomak_scraper import StokomakScraper
from typing import Optional
from .base_market_scraper import BaseMarketScraper


def get_market_scraper(
    market_name: str,
    base_url: str,
    browser: str,
    headless: bool,
    per_page_limit: Optional[int] = None,
    total_limit: Optional[int] = None,
) -> BaseMarketScraper:
    """
    Factory function to get a scraper instance for a given market.

    Args:
        market_name: The name of the market (e.g., 'vero').
        base_url: The base URL for the market's website.
        browser: The browser to use ('edge', 'chrome', 'firefox').
        headless: Whether to run the browser in headless mode.
        per_page_limit: The limit of products to scrape per page.
        total_limit: The total limit of products to scrape.

    Returns:
        An instance of a BaseMarketScraper subclass.
    """
    scrapers = {
        "vero": VeroScraper,
        "tinex": TinexScraper,
        "zito": ZitoScraper,
        "stokomak": StokomakScraper,
    }

    scraper_class = scrapers.get(market_name.lower())

    if scraper_class:
        return scraper_class(
            base_url=base_url,
            browser=browser,
            headless=headless,
            per_page_limit=per_page_limit,
            total_limit=total_limit,
        )
    else:
        raise ValueError(f"Scraper for market '{market_name}' not found.")
