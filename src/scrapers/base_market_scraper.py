# -*- coding: utf-8 -*-
import time
import os
import json
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Овие две датотеки треба да бидат во src/utils/
from src.utils.helpers import handle_selenium_error, random_delay


class BaseMarketScraper(ABC):
    """
    A base class for market scrapers.
    This version is implemented according to the user's specific instructions:
    1. Get all market IDs from the initial dropdown.
    2. Loop through each market ID.
    3. For each market, loop through pages by incrementing 'page' in the URL.
    4. Stop when a page shows "Нема артикли".
    """
    def __init__(
        self,
        base_url: str,
        market_name: str,
        browser: str = 'chrome',
        headless: bool = True,
        per_page_limit: Optional[int] = None, # Note: This is less relevant with the new logic
        total_limit: Optional[int] = None
    ):
        self.base_url = base_url.split('?')[0] # Get the clean base URL without any params
        self.market_name = market_name
        self.browser = browser.lower()
        self.headless = headless
        self.per_page_limit = per_page_limit
        self.total_limit = total_limit
        self.logger = logging.getLogger(f"{self.__class__.__name__}({market_name})")
        self.total_products_scraped = 0
        
        # This will store details like {'id': '2', 'name': '2 Трговски - Велес'}
        self.market_details: List[Dict[str, str]] = []

        self.logger.info(f"Initializing WebDriver for browser: {self.browser}")
        options = None
        if self.browser == 'chrome':
            options = ChromeOptions()
        elif self.browser == 'edge':
            options = EdgeOptions()
        elif self.browser == 'firefox':
            options = FirefoxOptions()

        if options is not None:
            if self.headless:
                options.add_argument("--headless")
            # Add arguments to make the scraper more robust
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            self.driver = (
                webdriver.Chrome(options=options)
                if self.browser == 'chrome'
                else webdriver.Edge(options=options)
                if self.browser == 'edge'
                else webdriver.Firefox(options=options)
            )
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_market_details(self) -> List[Dict[str, str]]:
        """
        Step 1: Get all market 'value' attributes and names from the dropdown.
        """
        self.logger.info("Navigating to the base URL to get market details...")
        self.driver.get(self.base_url)
        markets = []
        try:
            dropdown_element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='org']"))
            )
            market_dropdown = Select(dropdown_element)
            
            options = [opt for opt in market_dropdown.options if opt.get_attribute('value')]
            
            for opt in options:
                market_id = opt.get_attribute('value')
                market_name = opt.text.strip()
                markets.append({'id': market_id, 'name': market_name})

            self.logger.info(f"Successfully found {len(markets)} markets to scrape.")
        except Exception as e:
            self._handle_error(e, "getting_market_details_from_dropdown")
        return markets

    def scrape(self) -> List[str]:
        """
        Main scraping method.
        - Loops through markets and their pages.
        - Passes the per_page_limit to the extraction function.
        - Obeys the total_limit to stop all operations.
        """
        self.logger.info(f"Starting scrape for {self.market_name}...")
        all_products: List[Dict[str, Any]] = []
        output_files: List[str] = []

        self.market_details = self._get_market_details()
        if not self.market_details:
            self.logger.error("Could not retrieve market details. Stopping scrape.")
            return []

        # A flag to break out of the outer loop once the total limit is met
        stop_scraping_total = False

        for market in self.market_details:
            if stop_scraping_total:
                break
                
            market_id = market['id']
            market_name_text = market['name']
            self.logger.info(f"--- Starting scrape for Market: {market_name_text} (ID: {market_id}) ---")
            
            page_num = 1
            
            while True:
                # Check 1: TOTAL limit. If met, stop fetching new pages.
                if self.total_limit is not None and self.total_products_scraped >= self.total_limit:
                    self.logger.info(f"Total product limit of {self.total_limit} reached. Stopping all scraping.")
                    stop_scraping_total = True
                    break

                page_url = f"{self.base_url}?org={market_id}&search=&perPage=20&page={page_num}"
                self.logger.info(f"Scraping Page {page_num} from URL: {page_url}")

                self.driver.get(page_url)
                
                # Check for the end-of-market message
                if "Нема артикли по зададените критериуми" in self.driver.page_source:
                    self.logger.info(f"End of products for market '{market_name_text}'. Moving to the next market.")
                    break

                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.table-responsive .table'))
                    )
                except TimeoutException:
                    self.logger.warning(f"Table not found on {page_url}. Assuming end of pages.")
                    break
                
                # Call the extraction method, passing the per-page limit down to it.
                page_products = self._extract_products_from_page(
                    market_id,
                    market_name_text,
                    self.per_page_limit
                )
                
                # Add the collected products (if any) to our main list
                all_products.extend(page_products)
                
                # If the extraction returned nothing, it might be because the total limit was hit
                # inside of it. In any case, there's no need to continue with this market.
                if not page_products and self.total_limit is not None and self.total_products_scraped >= self.total_limit:
                    # This ensures we break the page loop if the limit was hit mid-page
                    self.logger.info("Total limit reached during page extraction. Stopping market scrape.")
                    stop_scraping_total = True
                    break

                # --- НОВ УСЛОВ ЗА ИЗЛЕЗ ---
                # Ако листата е празна, прекини го циклусот.
                if not page_products: # Ова е исто како 'if len(page_products) == 0:'
                    self.logger.info("Страницата не врати продукти, се претпоставува крај.")
                    break
                
                # Increment page number for the next loop
                page_num += 1
                random_delay()

        # --- SAVING DATA AT THE END ---
        if all_products:
            # A final trim is good practice to strictly enforce the total_limit
            if self.total_limit is not None and len(all_products) > self.total_limit:
                all_products = all_products[:self.total_limit]
                
            output_file = self._save_data(all_products)
            output_files.append(output_file)
            self.logger.info(
                f"Scrape successful. Saved {len(all_products)} products to {output_file}."
            )
        else:
            self.logger.warning("Scrape completed, but no products were found.")

        return output_files

    def _extract_products_from_page(self, market_id: str, market_name: str, per_page_limit: Optional[int]) -> List[Dict[str, Any]]:
        """
        Extracts products row-by-row.
        - Obeys the total_limit.
        - Obeys the per_page_limit by stopping after collecting that many items from THIS PAGE.
        """
        products: List[Dict[str, Any]] = []
        
        # Return immediately if the total limit is already met
        if self.total_limit is not None and self.total_products_scraped >= self.total_limit:
            return []

        try:
            # --- НОВ ДЕЛ: ПРОВЕРКА ЗА "НЕМА ПОДАТОЦИ" ---
            # Бараме ќелија (td) која го содржи текстот. find_elements не фрла грешка ако не најде ништо.
            no_data_elements = self.driver.find_elements(By.XPATH, "//td[contains(text(), 'Нема податоци за прикажување')]")
            
            if no_data_elements:
                self.logger.info(f"Пронајдена порака 'Нема податоци'. Крај на собирањето за '{market_name}'.")
                return []  # Врати None за да му сигнализираш на повикувачкиот циклус дека е крај.
            # --- КРАЈ НА НОВИОТ ДЕЛ ---

            rows = self.driver.find_elements(By.CSS_SELECTOR, 'div.table-responsive .table tbody tr')
            if not rows:
                return []

            table = self.driver.find_element(By.CSS_SELECTOR, 'div.table-responsive .table')
            headers = [
                th.text.strip().lower().replace(' ', '_').replace('\n', '_')
                for th in table.find_elements(By.CSS_SELECTOR, 'thead th')
            ]

            for row in rows:
                # Check 1: The ABSOLUTE total limit. If this is hit, we are done completely.
                if self.total_limit is not None and self.total_products_scraped >= self.total_limit:
                    self.logger.info(f"Total limit ({self.total_limit}) reached. Stopping all extractions.")
                    return products

                # Check 2: The limit FOR THIS PAGE ONLY.
                # If we have collected enough products from this page, break the loop and move to the next page.
                if per_page_limit is not None and len(products) >= per_page_limit:
                    self.logger.info(f"Per-page limit of {per_page_limit} reached for this page. Moving on.")
                    break # This breaks the 'for row in rows' loop

                # --- If no limits are hit, process the row ---
                cells = row.find_elements(By.TAG_NAME, 'td')

                # check if 
                item = {headers[i]: cells[i].text.strip() for i in range(len(cells))}
                # add log for item
                self.logger.debug(f"Raw product data: {item}")

                # --- Raw Validation Step ---
                if not self._is_raw_product_valid(item):
                    continue # Skip this product if it's invalid
                # --- End Raw Validation ---

                item['market_id'] = market_id
                item['market_name'] = market_name
                item['scraped_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
                products.append(item)
                # Increment the master counter only after successfully adding a product
                self.total_products_scraped += 1 

        except Exception as e:
            self._handle_error(e, f"extracting_products_from_market_{market_id}")
            
        # add log for total products scraped for this market
        self.logger.info(f"Total products scraped for market {market_name}: {self.total_products_scraped}")
        return products
    
    def _save_data(self, data: List[Dict[str, Any]]) -> str:
        """Saves data to a JSON file and returns the file path."""
        filename = f"outputs/{self.market_name.lower()}_raw_data.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.logger.info(f"Successfully saved {len(data)} items to {filename}")
        return filename

    def _handle_error(self, e: Exception, context: str):
        """Centralized error handler using the generic helper."""
        handle_selenium_error(self.driver, self.logger, e, context)

    def close(self):
        """Closes the Selenium WebDriver."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            self.logger.info("Browser closed.")

    def _is_raw_product_valid(self, product: Dict[str, Any]) -> bool:
        """
        Performs basic validation on the raw scraped product data.
        """
        name = product.get('назив_на_стока-производ', '').strip()
        current_price_str = product.get('продажна_цена', '').strip()
        
        # 1. Product name must not be empty
        if not name:
            self.logger.warning(f"Skipping product with empty name.")
            return False

        # 2. Product name must contain at least one letter or number
        if not re.search(r'[\w]', name, re.UNICODE):
            self.logger.warning(f"Skipping product with name containing only special characters: '{name}'")
            return False

        # 3. Current price must not be empty
        if not current_price_str:
            self.logger.warning(f"Skipping product '{name}' due to empty price.")
            return False

        # 4. Prices must be positive numbers
        try:
            # A simple helper to clean the price string for validation
            price_clean = re.sub(r'[^\d,.]', '', current_price_str).replace(',', '.')
            price_val = float(price_clean)
            if price_val <= 0:
                self.logger.warning(f"Skipping product '{name}' with non-positive price: {price_val}")
                return False
        except (ValueError, TypeError):
            self.logger.warning(f"Skipping product '{name}' with unparseable price: '{current_price_str}'")
            return False
            
        # All checks passed
        return True