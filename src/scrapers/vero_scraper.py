# -*- coding: utf-8 -*-
from .base_market_scraper import BaseMarketScraper
from typing import List, Dict, Any, Optional
import time
import re
import logging
import json
import os
from src.utils.helpers import random_delay
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class VeroScraper(BaseMarketScraper):
    """A scraper for the Vero supermarket website."""

    def __init__(
        self,
        base_url: str,
        browser: str = "chrome",
        per_page_limit: Optional[int] = None,
        total_limit: Optional[int] = None,
        headless: bool = True,
    ):
        """
        Initializes the VeroScraper.

        Args:
            base_url (str): The base URL for the Vero market's price checker website.
            browser (str, optional): The browser to use for Selenium automation ('chrome', 'firefox', 'edge'). Defaults to 'chrome'.
            per_page_limit (Optional[int], optional): The maximum number of products to scrape per page. Defaults to None (no limit).
            total_limit (Optional[int], optional): The total maximum number of products to scrape across all pages/markets. Defaults to None (no limit).
            headless (bool, optional): Whether to run the browser in headless mode (no UI). Defaults to True.
        """
        super().__init__(
            base_url=base_url,
            market_name="Vero",
            browser=browser,
            per_page_limit=per_page_limit,
            total_limit=total_limit,
            headless=headless,
        )
        self.market_code_to_name = {}

    def scrape(self) -> List[str]:
        """Orchestrates the scraping process for the Vero supermarket.

        This method locates all market URLs, scrapes product data from each market,
        aggregates the results, and saves the combined data to a file.

        Returns:
            List[str]: A list containing the path to the saved data file. Returns an empty
                list if no data was scraped or if an error occurred.
        """
        self.logger.info("Starting Vero scrape process.")

        # 1. --- Get market URLs ---
        market_urls = self._get_market_urls()
        if not market_urls:
            self.logger.error("No market URLs found. Aborting scrape.")
            return []

        all_market_products = []
        for url in market_urls:
            if self.total_limit and self.total_products_scraped >= self.total_limit:
                self.logger.info("Total product limit reached. Stopping scrape.")
                break
            # 2. --- Scrape products from the market's page ---
            products_from_url = self._scrape_products_from_url(url)
            all_market_products.extend(products_from_url)

        if not all_market_products:
            self.logger.warning("Scraping complete, but no products were found.")
            return []

        # Save the aggregated data to a single file
        output_file = self._save_data(all_market_products)
        self.logger.info(f"Vero scrape process finished. Data saved to {output_file}")
        return [output_file]

    def _get_market_urls(self, retries: int = 3) -> list:
        """Finds all individual market links on the homepage.

        Handles potential cookie banners and retries on timeout.

        Args:
            retries (int): Number of times to retry loading the market links if not found.

        Returns:
            list: A list of URLs (str) for each market found on the homepage.
        """
        self.logger.info("Navigating to the base URL to find market links...")
        self.driver.get(self.base_url)

        for attempt in range(retries):
            try:
                # Attempt to click the cookie consent button if it exists
                try:
                    cookie_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Прифати ги сите')]")
                        )
                    )
                    self.logger.info(
                        f"Attempt {attempt + 1}: Cookie consent button found. Clicking it..."
                    )
                    cookie_button.click()
                    time.sleep(2)  # Wait a moment for the banner to disappear
                except Exception:
                    self.logger.warning(
                        f"Attempt {attempt + 1}: Cookie button not found or clickable. Continuing..."
                    )

                # Wait until at least one market link is present
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "table a[href$='.html']")
                    )
                )
                self.logger.info(
                    f"Attempt {attempt + 1}: Market links appear to be present on the page."
                )

                # Find all the market links using a pure Selenium approach
                links = self.driver.find_elements(
                    By.CSS_SELECTOR, "table a[href$='.html']"
                )
                if not links:
                    self.logger.warning(
                        f"Attempt {attempt + 1}: Waited for links, but find_elements returned none. Retrying..."
                    )
                    self.driver.refresh()
                    random_delay(2, 4)
                    continue

                # Process the found links
                urls = set()
                for link in links:
                    href = link.get_attribute("href")
                    if href:
                        # Use urljoin for robustly handling relative URLs
                        full_url = urljoin(self.base_url, href)
                        urls.add(full_url)

                        # Extract market code and name
                        match = re.search(r"/(\d+)_", href)
                        if match:
                            market_code = match.group(1)
                            market_name = (
                                f"Market_{market_code}"  # Default fallback name
                            )
                            try:
                                # Find the parent of the link, then find the h1 inside it
                                parent_element = link.find_element(By.XPATH, "..")
                                name_element = parent_element.find_element(
                                    By.TAG_NAME, "h1"
                                )
                                name_text = name_element.text.strip()
                                if name_text:
                                    market_name = name_text
                            except Exception:
                                self.logger.warning(
                                    f"Could not find h1 name for market code {market_code}. Using fallback."
                                )

                            if market_code not in self.market_code_to_name:
                                self.market_code_to_name[market_code] = market_name
                                self.logger.info(
                                    f"Found market: Code='{market_code}', Name='{market_name}'"
                                )

                # Save the market map to a file
                map_path = "outputs/vero_market_map.json"
                os.makedirs(os.path.dirname(map_path), exist_ok=True)
                with open(map_path, "w", encoding="utf-8") as f:
                    json.dump(self.market_code_to_name, f, ensure_ascii=False, indent=4)
                self.logger.info(
                    f"Market map saved with {len(self.market_code_to_name)} entries."
                )

                return list(urls)

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    self.logger.info("Refreshing page and retrying...")
                    self.driver.refresh()
                    random_delay(3, 5)
                else:
                    self.logger.error(
                        "All attempts to find market links have failed.", exc_info=True
                    )
                    self._handle_error(e, "finding_market_links_after_retries")

        # If all retries fail, save a debug snapshot before returning
        self.logger.error("Could not find market URLs. Saving debug snapshot.")
        self._save_debug_snapshot("market_links_not_found")
        return []  # Return empty list if all retries fail

    def _scrape_products_from_url(self, url: str) -> List[Dict[str, Any]]:
        """Scrape all products from a given market page URL and its subsequent pages.

        This method implements the abstract method from the base class. It navigates through
        the paginated product listings for a specific market, extracting product data from each
        page until there are no more products or a product limit is reached.

        Args:
            url (str): The URL of the first product page for the market.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a product scraped
                from the market's pages.
        """
        all_products = []
        current_url = url
        page_num = 1

        match = re.search(r"/(\d+)_", url)
        market_code = match.group(1) if match else "unknown"

        while True:
            # Check if total limit has been reached before fetching a new page
            if (
                self.total_limit is not None
                and self.total_products_scraped >= self.total_limit
            ):
                self.logger.info(
                    f"Total product limit reached while scraping market {market_code}. Stopping."
                )
                break

            self.logger.info(f"Scraping page: {current_url}")

            # 3. --- Navigate to the page ---
            success = self._navigate_to_page(current_url) 
            if not success:
                break

            # 4. --- Extract products from the market's page ---
            page_products = self._extract_products_from_page(market_code)

            if not page_products:
                self.logger.info(
                    f"No products found on {current_url}. Assuming end of this market's pages."
                )
                break

            all_products.extend(page_products)

            page_num += 1
            current_url = re.sub(r"_\d+\.html$", f"_{page_num}.html", current_url)
            random_delay()

        self.logger.info(
            f"Finished scraping for market code '{market_code}' from URL '{url}'. Found {len(all_products)} products."
        )
        return all_products

    def _navigate_to_page(self, url: str, retries: int = 3) -> bool:
        """Navigates to a URL and waits for the product table, with retries.

        Args:
            url (str): The URL to navigate to.
            retries (int): Number of times to retry if the page is not found.

        Returns:
            bool: True if the page was successfully navigated to, False otherwise.
        """
        for attempt in range(retries):
            try:
                self.driver.get(url) # Navigate to the page using Selenium WebDriver's GET mechanism!
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'table[style*="font-size: 13"]')
                    )
                )
                return True
            except Exception as e:
                # Check for 404 specifically
                if (
                    "404 Not Found" in self.driver.page_source
                    or "The requested URL was not found on this server"
                    in self.driver.page_source
                ):
                    self.logger.info(
                        f"Page {url} returned 404. This is the end of the pages for this market."
                    )
                    return False

                self.logger.warning(
                    f"Attempt {attempt + 1}/{retries} failed for {url}: {e}"
                )
                if attempt < retries - 1:
                    random_delay(2, 5)
                else:
                    self._handle_error(e, context=f"scraping_page_{url.split('/')[-1]}")
                    self._save_debug_snapshot(
                        f"page_navigation_failed_{url.split('/')[-1]}"
                    )
        return False

    def _save_debug_snapshot(self, context_name: str):
        """Saves a screenshot and the page source for debugging.

        Args:
            context_name (str): The name of the context for the snapshot.
        """
        try:
            # Sanitize context_name to be a valid filename
            safe_context = re.sub(r"[^a-zA-Z0-9_-]", "_", context_name)

            # Create timestamped filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_dir = "error_screenshots"
            os.makedirs(output_dir, exist_ok=True)

            # Save screenshot
            screenshot_path = os.path.join(
                output_dir, f"{safe_context}_{timestamp}.png"
            )
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Saved error screenshot to {screenshot_path}")

            # Save page source
            html_path = os.path.join(output_dir, f"{safe_context}_{timestamp}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.logger.info(f"Saved error page source to {html_path}")

        except Exception as ss_e:
            self.logger.error(f"Could not save debug snapshot: {ss_e}")

    def _is_raw_product_valid(self, product: Dict[str, Any]) -> bool:
        """Performs basic validation on the raw scraped product data.

        Args:
            product (Dict[str, Any]): A dictionary representing a scraped product.

        Returns:
            bool: True if the product data is valid, False otherwise.
        """
        name = product.get("назив_на_стока", "").strip()
        current_price_str = product.get("продажна_цена\n(со_ддв)", "").strip()

        # 1. Product name must not be empty
        if not name:
            self.logger.warning("Skipping product with empty name.")
            return False

        # 2. Product name must contain at least one letter or number
        if not re.search(r"[\w]", name, re.UNICODE):
            self.logger.warning(
                f"Skipping product with name containing only special characters: '{name}'"
            )
            return False

        # 3. Current price must not be empty
        if not current_price_str:
            self.logger.warning(f"Skipping product '{name}' due to empty price.")
            return False

        # 4. Prices must be positive numbers
        try:
            # A simple helper to clean the price string for validation
            price_clean = re.sub(r"[^\d,.]", "", current_price_str).replace(",", ".")
            price_val = float(price_clean)
            if price_val <= 0:
                self.logger.warning(
                    f"Skipping product '{name}' with non-positive price: {price_val}"
                )
                return False
        except (ValueError, TypeError):
            self.logger.warning(
                f"Skipping product '{name}' with unparseable price: '{current_price_str}'"
            )
            return False

        # All checks passed
        return True

    def _extract_products_from_page(self, market_code: str) -> List[Dict[str, Any]]:
        """Extracts all rows from the product table on the current page.

        Args:
            market_code (str): The code of the market being scraped.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a scraped product.
        """
        products = []
        try:
            table = self.driver.find_element(
                By.CSS_SELECTOR, 'table[style*="font-size: 13"]'
            )

            header_row = table.find_element(By.CSS_SELECTOR, 'tr[bgcolor="silver"]')
            headers = [
                th.text.strip().lower().replace(" ", "_")
                for th in header_row.find_elements(By.TAG_NAME, "th")
            ]

            if not headers:
                self.logger.error("Could not find table headers.")
                return []

            rows = table.find_elements(By.XPATH, './/tr[not(@bgcolor="silver")]')

            for row in rows:
                if (
                    self.per_page_limit is not None
                    and len(products) >= self.per_page_limit
                ):
                    self.logger.info(f"Reached per-page limit ({self.per_page_limit}).")
                    break

                if (
                    self.total_limit is not None
                    and (self.total_products_scraped + len(products))
                    >= self.total_limit
                ):
                    self.logger.info(
                        f"Approaching total product limit ({self.total_limit}). Stopping extraction on this page."
                    )
                    break

                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == len(headers):
                    product_data = {
                        headers[i]: cells[i].text.strip() for i in range(len(cells))
                    }

                    # --- Raw Validation Step ---
                    if not self._is_raw_product_valid(product_data):
                        continue  # Skip this product if it's invalid
                    # --- End Raw Validation ---

                    product_data["market_code"] = market_code
                    product_data["market_name"] = self.market_code_to_name.get(
                        market_code, "Unknown"
                    )
                    product_data["scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    products.append(product_data)
                    self.total_products_scraped += 1 # HERE
        except Exception as e:
            self._handle_error(
                e, context=f"extracting_products_from_market_{market_code}"
            )

        self.logger.info(
            f"Found {len(products)} valid products on current page for market {market_code}."
        )
        return products


if __name__ == "__main__":
    # This block allows for direct testing of the VeroScraper.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    VERO_BASE_URL = "https://pricelist.vero.com.mk/"
    TEST_PRODUCT_LIMIT = 50
    IS_HEADLESS = False

    logging.info("--- Starting direct test run for VeroScraper ---")

    try:
        with VeroScraper(
            base_url=VERO_BASE_URL, total_limit=TEST_PRODUCT_LIMIT, headless=IS_HEADLESS
        ) as test_scraper:
            output_files = test_scraper.scrape()
            if output_files:
                logging.info(
                    f"VeroScraper direct test run finished successfully. Data saved to: {output_files}"
                )
            else:
                logging.warning(
                    "VeroScraper test run completed, but no data was saved."
                )

    except Exception as e:
        logging.error(
            f"An error occurred during the direct test run: {e}", exc_info=True
        )
