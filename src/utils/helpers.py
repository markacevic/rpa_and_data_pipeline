import os
import json
import logging
from datetime import datetime
from typing import Any, Dict
import random
import time
from selenium.webdriver.remote.webdriver import WebDriver

def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_output_dir(dir_path: str) -> None:
    """Create output directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def save_json(data: Dict[str, Any], filepath: str) -> None:
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filepath: str) -> Dict[str, Any]:
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_timestamp() -> str:
    """Get current timestamp in a formatted string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def format_filename(base_name: str, extension: str) -> str:
    """Format filename with timestamp."""
    timestamp = get_timestamp()
    return f"{base_name}_{timestamp}.{extension}"

def random_delay(min_sec=1.5, max_sec=4.0):
    """Waits for a random duration to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    logging.info(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def handle_selenium_error(driver: WebDriver, logger: logging.Logger, e: Exception, context: str):
    """
    A generic error handler for Selenium scrapers. Logs the error and saves a screenshot.
    """
    logger.error(f"An error occurred during {context}: {e}", exc_info=True)
    try:
        screenshots_dir = "error_screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        safe_context = context.replace('/', '_').replace(':', '')
        screenshot_file = os.path.join(screenshots_dir, f"{safe_context}_{timestamp}.png")
        driver.save_screenshot(screenshot_file)
        logger.info(f"Saved screenshot for debugging to: {screenshot_file}")
    except Exception as screenshot_error:
        logger.error(f"Could not save screenshot: {screenshot_error}") 